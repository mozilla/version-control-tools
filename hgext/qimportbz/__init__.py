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
from mercurial import hg, commands, cmdutil, extensions, url, error, httppeer
from hgext import mq

import re
import os
import urllib

import bz
import bzhandler
import pb
import scp

def extsetup(ui=None):
  # "Mercurial version 8e6019b16a7d and later (that is post-1.3.1) will pass a
  # ui argument to extsetup."
  # 'None': support pre/post Hg v1.3.1 versions.

  # Insert preview flag into qimport:
  # For HG 1.3.1 and earlier, commands.table has the commands for mq
  # For HG 1.4, commands.table does not have the commands for mq so we
  #   use mq.cmdtable
  #
  # Note that we cannot just use mq.cmdtable always because each command entry
  # is a tuple so wrapping the qimport function will not update the right
  # table
  #
  # Hence our strategy is to try commands.table and fall back to mq.cmdtable
  # rather than do an explicit version check.
  try:
    qimport_cmd = cmdutil.findcmd("qimport", commands.table)
    cmdtable = commands.table
  except error.UnknownCommand:
    qimport_cmd = cmdutil.findcmd("qimport", mq.cmdtable)
    cmdtable = mq.cmdtable
  qimport_cmd[1][1].append(('p', 'preview', False, "preview commit message"))

  # re to match our url syntax
  bz_matcher = re.compile("bz:(?://)?(\d+)(?:/(\w+))?")
  pb_matcher = re.compile("pb:(?://)?(\d+)")
  scp_matcher= re.compile(r"scp:(?://)?(.*)")

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
    def checkpatchname(patch):
      name = patch.name
      # Hg v1.4+: "ui.prompt is now a simple prompt and does not accept a list of choices. Use ui.promptchoice instead.".
      hasPromptchoice = hasattr(ui, 'promptchoice')
      while os.path.exists(q.join(name)):
        prompt = "A patch file named '%s' already exists in your patch directory. Rename %s '%s' (%d) (r)/overwrite (o)?" % \
                 (name,
                  'patch' if isinstance(patch, bz.Patch) else 'attachment',
                  patch.desc,
                  int(patch.id))
        if hasPromptchoice:
          choice = ui.promptchoice(prompt,
                                   ("&readonly", "&overwrite"),
                                   0)
          choice = ["r", "o"][choice]
        else:
          choice = ui.prompt(prompt,
                             ("&readonly", "&overwrite"),
                             "r")
        if choice == 'r':
          name = ui.prompt("Enter the new patch name (old one was '%s'):" % name)
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

    # Remember where the next patch will be inserted into the series
    try:
      # hg 1.9+
      insert = q.fullseriesend()
    except:
      insert = q.full_series_end()

    # Do the import as normal. The first patch of any bug is actually imported
    # and the rest are stored in the global delayed_imports. The imported
    # patches have dumb filenames because there's no way to tell mq to pick the
    # patch name *after* download.
    orig(ui, repo, *files, **opts)

    # If the user passed a name, then mq used that so we don't need to rename
    if not opts['name']:
      # cache the lookup of the name. findcmd is not fast.
      qrename = cmdutil.findcmd("qrename", commands.table)[1][0]

      # For all the already imported patches, rename them. Except there will
      # only be one, since if the url resolves to multiple patches then
      # everything but the first will go into bzhandler.delayed_imports.
      for (patch, path) in list(bzhandler.imported_patches):
        # Find where qimport will have inserted the initial patch
        try:
          # hg 1.9+
          oldpatchname = q.fullseries[insert]
        except:
          oldpatchname = q.full_series[insert]
        insert += 1
        newpatchname = checkpatchname(patch)
        if newpatchname != oldpatchname:
          qrename(ui, repo, oldpatchname, newpatchname)
          # mq always reports the original name, which is confusing so we'll
          # report the rename. But if ui.verbose is on, qrename will have
          # already reported it.
          if not ui.verbose:
            ui.write("renamed %s -> %s\n" % (oldpatchname, newpatchname))

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

  extensions.wrapcommand(cmdtable, 'qimport', qimporthook)

  # Here we setup the protocol handlers
  processors = {
    'bz' : bzhandler.Handler,
    'pb' : pb.Handler,
    'scp' : scp.Handler
  }

  # Mercurial 1.4 has an easy way to do this for bz://dddddd urls
  if hasattr(url, 'handlerfuncs') and hasattr(hg, 'schemes'):
    for s, p in processors.items():
      url.handlerfuncs.append(p)
      hg.schemes[s] = httppeer
  else: # monkey patching for 1.3.1 :(
    # patch in bz: and pb: url support
    def bzopener(orig, ui, authinfo=None):
      result = orig(ui, authinfo)
      for p in processors:
        result.add_handler(p(ui, authinfo))
      return result

    extensions.wrapfunction(url, "opener", bzopener)
