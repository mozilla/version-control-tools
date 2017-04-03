"""qimportbz

Imports patches from bugzilla to your mercurial queue

Example:

  hg qimport bz://1234567

Configuration section is entirely optional but potentially useful::

  [qimportbz]
  bugzilla = server-address (defaults to BUGZILLA environment varable or bugzilla.mozilla.org)
  joinstr = string to join flags for commit messages (default is ' ')
  patch_format = Formatting string used to create patch names automatically. Set it to empty to use the initial filename.
  msg_format = Formatting string used to create commit messages automatically
  auto_choose_all = If multiple patches associated with a bug choose them all without prompting (default is False)

Formatting strings are the standard python format strings where a dictionary is used to supply the data.
For users of Mercurial 1.2: any % characters must be escaped since Python's configuration parser will try to interpret them.

There are 7 pieces of patch metadata available for use::

  "bugnum" : the bug number
  "id" : the patch id (internal bugzilla number)
  "title" : the bug title
  "desc" : the patch description
  "flags" : all the flags
  "filename" : the initial patch filename
  "bugdesc" : the bug description

The default values are::

  patch_format = %(filename)s
  msg_format = Bug %(bugnum)s - "%(title)s" [%(flags)s]
"""
from mercurial import hg, commands, cmdutil, extensions, url, httppeer
from hgext import mq

import re
import os
import urllib

import bz
import bzhandler
import pb
import scp

buglink = 'https://bugzilla.mozilla.org/enter_bug.cgi?product=Developer%20Services&component=Mercurial%3A%20qimportbz'
testedwith = '3.8 3.9 4.0 4.1'
minimumhgversion = '3.8'


def extsetup(ui):
    # Insert preview flag into qimport
    qimport_cmd = cmdutil.findcmd("qimport", mq.cmdtable)
    cmdtable = mq.cmdtable
    qimport_cmd[1][1].append(('p', 'preview', False, "preview commit message"))

    # re to match our url syntax
    bz_matcher = re.compile("bz:(?://)?(\d+)(?:/(\w+))?")
    pb_matcher = re.compile("pb:(?://)?(\d+)")
    scp_matcher = re.compile(r"scp:(?://)?(.*)")

    def makebzurl(num, attachid):
        return "bz://%s%s" % (num, "/" + attachid if attachid else "")

    def makepburl(num):
        return "pb://%s" % num

    def makescpurl(path):
        return "scp://%s" % urllib.quote(path, safe='')

    def fixuppath(path):
        m = bz_matcher.search(path)
        if m:
            bug, attachment = m.groups()
            return makebzurl(bug, attachment)

        m = pb_matcher.search(path)
        if m:
            num, = m.groups()
            return makepburl(num)

        m = scp_matcher.search(path)
        if m:
            scppath, = m.groups()
            return makescpurl(scppath)

        return path

    # hook the mq import so we can fixup the patchname and handle multiple
    # patches per url
    def qimporthook(orig, ui, repo, *files, **opts):
        q = repo.mq

        # checks for an unused patch name. prompts if the patch already exists and
        # returns the corrected name.
        def checkpatchname(patch, current_filename=None):
            name = patch.name
            # For the first patch imported, the patch has already been temporarily saved
            # to disk by the time we reach here, with a filename that we cannot control
            # (eg 973703 for bz://973703). The patch is then renamed by us to the name of
            # the attachment in Bugzilla (unless patch_format has been overridden).
            # Unfortunately it's common for people to use the bug number as the filename of
            # the attachment, which would cause a name collision with this temporary file.
            # Patches other than the first will not have a current_filename.
            if name == current_filename:
                # Add a suffix to the patch filename to avoid a collision. This is preferable
                # to just skipping the check to see if the file exists, since if we leave the
                # filename as-is, subsequent qimports of the same bug will abort with an mq
                # "patch already exists" when it is unable to write its temporary file.
                ui.status("Changing patch filename to avoid conflict with temporary file.\n")
                name = "%s_" % name
            while os.path.exists(q.join(name)):
                msg = ("A file named '%s' already exists in your patch directory.\n"
                       "Rename %s '%s' (%d) (r)/overwrite (o)?" %
                       (name,
                        'patch' if isinstance(patch, bz.Patch) else 'attachment',
                        patch.desc,
                        int(patch.id)))
                if name in q.series and q.isapplied(name):
                    ui.write("A patch file named '%s' is already applied.\n")
                    choice = 'r'
                else:
                    choice = ui.prompt(msg, default="r")
                if choice == 'r':
                    name = ui.prompt("Enter the new patch name (old one was '%s'):" % name, default=name)
                else:
                    # overwrite
                    break
            if name in q.series and q.isapplied(name):
                ui.fatal("Patch with that name is already applied.")
            return name

        # hook for url.open which lets the user edit the returned patch name
        def previewopen(orig, ui, path):
            fp = orig(ui, path)

            class PreviewReader(object):
                def read(self):
                    return ui.edit(fp.read(), ui.username())

            return PreviewReader()

        # Install the preview hook if necessary. This will preview non-bz:// bugs
        # and that's OK.
        if opts['preview']:
            extensions.wrapfunction(url, "open", previewopen)

        # mercurial's url.search_re includes the // and that doesn't match what we
        # want which is bz:dddddd(/ddddd)?
        files = map(fixuppath, files)

        # Do the import as normal. The first patch of any bug is actually imported
        # and the rest are stored in the global delayed_imports. The imported
        # patches have dumb filenames because there's no way to tell mq to pick the
        # patch name *after* download.
        ret = orig(ui, repo, *files, **opts)
        if ret or bzhandler.last_imported_patch() is None:
            return ret

        # If the user passed a name, then mq used that so we don't need to rename
        if not opts['name']:
            # cache the lookup of the name. findcmd is not fast.
            qrename = cmdutil.findcmd("qrename", commands.table)[1][0]

            # Rename the already imported patch. If there are multiple patches, the
            # rest will be in bzhandler.delayed_imports, which we'll name correctly
            # in the first place.
            oldpatchname = q.fullseries[q.fullseriesend()]
            newpatchname = checkpatchname(bzhandler.last_imported_patch(), current_filename=oldpatchname)
            if newpatchname != oldpatchname:
                if newpatchname in q.series:
                    q.delete(repo, [newpatchname], {})
                qrename(ui, repo, oldpatchname, newpatchname)
                # mq always reports the original name, which is confusing so we'll
                # report the rename. But if ui.verbose is on, qrename will have already
                # reported it.
                if not ui.verbose:
                    ui.status("renamed %s -> %s\n" % (oldpatchname, newpatchname))

        # now process the delayed imports

        # these opts are invariant for all patches
        newopts = {}
        newopts.update(opts)
        newopts['force'] = True

        # loop through the Patches and import them by calculating their url. The
        # bz:// handler will have cached the lookup so we don't hit the network
        # here. Each one of these pushes an unapplied patch onto the beginning of
        # the queue, and unapplied patches are ignored when importing them, so do
        # these in reverse order.
        for patch in reversed(list(bzhandler.delayed_imports)):
            newopts['name'] = checkpatchname(patch)
            path = makebzurl(patch.bug.num, patch.id)

            ret = orig(ui, repo, path, **newopts)
            if ret:
                return ret

    extensions.wrapcommand(cmdtable, 'qimport', qimporthook)

    # Here we setup the protocol handlers
    processors = {
        'bz': bzhandler.Handler,
        'pb': pb.Handler,
        'scp': scp.Handler
    }

    for s, p in processors.items():
        url.handlerfuncs.append(p)
        hg.schemes[s] = httppeer
