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
from mercurial import commands, cmdutil, extensions

import re
import os

import bz
import bzhandler

def extsetup():
  qimport_cmd = cmdutil.findcmd("qimport", commands.table)
  qimport_cmd[1][1].append(('p', 'preview', False, "Preview commit message"))

  # Now we hook qimport
  bz_matcher = re.compile("bz:(?://)?(\d+)(?:/(\w+))?")
  def isbzurl(url):
    return bz_matcher.search(url) is not None
  def makeurl(num, attachid):
      return "bz://%s%s" % (num, "/" + attachid if attachid else "")
  def fixuppath(path):
    m = bz_matcher.search(path)
    if m:
      bug, attachment = m.groups()
      path = makeurl(bug, attachment)
    return path

  def checkpatchname(ui, repo, patch):
    q = repo.mq
    name = patch.name
    # Newer versions of mercurial have promptchoice but the latest release
    # (1.3.1) does not
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
    return name

  # and more monkey patching to hook the mq import so we can fixup the patchname
  def qimporthook(orig, ui, repo, *files, **opts):
    # mercurial's url.search_re includes the // and that doesn't match what we
    # want which is bz:dddddd(/ddddd)?
    files = map(fixuppath, files)

    # Do the import as normal. The first patch of any bug is actually imported
    # and the rest are stored in the global delayed_imports. The imported
    # patches have dumb filenames because there's no way to tell mq to pick the
    # patch name *after* download.
    orig(ui, repo, *files, **opts)

    qrename = cmdutil.findcmd("qrename", commands.table)[1][0]
    # For all the already imported patches, rename them
    for (patch,path) in list(bzhandler.imported_patches):
      # This mimcks the mq code to pick a filename
      oldpatchname = os.path.normpath(os.path.basename(path))
      newpatchname = checkpatchname(ui, repo, patch)

      qrename(ui, repo, oldpatchname, patch.name)

    # now process the delayed imports
    newopts = {}
    newopts.update(opts)
    newopts['force'] = True
    for patch in bzhandler.delayed_imports:
      newopts['name'] = checkpatchname(ui, repo, patch)
      path = makeurl(patch.bug.num, patch.id)

      orig(ui, repo, path, **newopts)

  extensions.wrapcommand(commands.table, 'qimport', qimporthook)

def reposetup(ui, repo):
  bzhandler.registerHandler(ui, repo)

cmdtable = {}

#cmdtable = {
#  "qimportbz" : (qimportbz,
#                 [('r', 'dry-run', False, "Perform a dry run - the patch queue will remain unchanged"),
#                  ('p', 'preview', False, "Preview commit message"),
#                  ('n', 'patch-name', '', "Override patch name")],
#                 "hg qimportbz [-v] [-r] [-p] [-n NAME] BUG#")
#}
