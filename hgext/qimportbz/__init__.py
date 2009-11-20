"""qimportbz

Imports patches from bugzilla to your mercurial queue

Configuration section is entirely optional but potentially useful.

[qimportbz]
bugzilla = server-address (defaults to BUGZILLA environment varable or bugzilla.mozilla.org)
joinstr = string to join flags for commit messages (default is ' ')
patch_format = Formatting string used to create patch names automatically
msg_format = Formatting string used to create commit messages automatically

Formatting strings are the standard python format strings where a dictionary is used to supply the data.
For users of Mercurial 1.2: any % characters must be escaped since Python's configuration parser will try to interpret them.

There are 5 pieces of patch metadata available for use:

      "bugnum" : the bug number
      "id" : the patch id (internal bugzilla number)
      "title" : the bug title
      "desc" : the patch description
      "flags" : all the flags

The default values are:
patch_format = bug-%(bugnum)s
msg_format = Bug %(bugnum)s - "%(title)s" [%(flags)s]
"""
from mercurial import commands, cmdutil, extensions, url

import re
import os
import urllib

import bz
import bzhandler
import pb
import scp

def extsetup():
  # insert preview flag into qimport
  qimport_cmd = cmdutil.findcmd("qimport", commands.table)
  qimport_cmd[1][1].append(('p', 'preview', False, "Preview commit message"))

  # re to match our url syntax
  bz_matcher = re.compile("bz:(?://)?(\d+)(?:/(\w+))?")
  pb_matcher = re.compile("pb:(?://)?(\d+)")
  scp_matcher= re.compile(r"scp:(?://)?(.*)")

  def makebzurl(num, attachid):
    return "bz://%s%s" % (num, "/" + attachid if attachid else "")

  def makepburl(num):
    return "pb://%s" % num

  def makescpurl(path):
    return "scp://%s" % urllib.pathname2url(path)

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
    def checkpatchname(patch):
      name = patch.name
      # Newer versions of mercurial have promptchoice but the latest release
      # (1.3.1) does not.
      prompter = ui.promptchoice if hasattr(ui, 'promptchoice') else ui.prompt
      while os.path.exists(q.join(name)):
        prompt = "A patch for bug %d already seems to exist in your patch directory. Rename %s '%s' (%d) (r)/overwrite (o)?" % \
                 (int(patch.bug.num),
                  'patch' if isinstance(patch, bz.Patch) else 'attachment',
                  patch.desc, int(patch.id))
        choice = prompter(prompt,
                          choices = ("&readonly", "&overwrite", "&cancel"),
                          default='o')
        if choice == 'r':
          name = ui.prompt("Enter the new patch name (old one was %s):" % name)
        else: # overwrite
          break;
      if name in q.series and q.isapplied(name):
        ui.warn("Patch was already applied. Changes will not take effect until the patch is reapplied.")
      return name

    # hook for url.open which lets the user edit the returned 
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
    orig(ui, repo, *files, **opts)

    # If the user passed a name, then mq used that so we don't need to rename
    if not opts['name']:
      # cache the lookup of the name. findcmd is not fast.
      qrename = cmdutil.findcmd("qrename", commands.table)[1][0]

      # For all the already imported patches, rename them
      for (patch, path) in list(bzhandler.imported_patches):
        # This mimcks the mq code to pick a filename
        oldpatchname = os.path.normpath(os.path.basename(path))
        newpatchname = checkpatchname(patch)

        qrename(ui, repo, oldpatchname, patch.name)

    # now process the delayed imports

    # these opts are invariant for all patches
    newopts = {}
    newopts.update(opts)
    newopts['force'] = True

    # loop through the Patches and import them by calculating their url. The
    # bz:// handler will have cached the lookup so we don't hit the network here
    for patch in bzhandler.delayed_imports:
      newopts['name'] = checkpatchname(patch)
      path = makebzurl(patch.bug.num, patch.id)

      orig(ui, repo, path, **newopts)

  extensions.wrapcommand(commands.table, 'qimport', qimporthook)

  # Here we setup the protocol handlers
  processors = [bzhandler.Handler, pb.Handler, scp.Handler]

  # Mercurial 1.4 has an easy way to do this for bz://dddddd urls
  if hasattr(url, 'handlerfuncs'):
    for p in processors:
      url.handlerfuncs.append(p)
  else: # monkey patching for 1.3.1 :(
    # patch in bz: and pb: url support
    def bzopener(orig, ui, authinfo=None):
      result = orig(ui, authinfo)
      for p in processors:
        result.add_handler(p(ui, authinfo))
      return result

    extensions.wrapfunction(url, "opener", bzopener)
