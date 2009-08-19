from mercurial import util
import bz
from StringIO import StringIO
import patch
import os
import re
import mercurial.commands

# Global so that I don't have to pass around this to everything
hgui = None
hgopts = {}

def cleanUserName(username):
  return re.sub("\(.*\)","", re.sub("\[:\w+\]|\(:\w+\)","",username)).strip()

def importPatch(ui, repo, p, opts):
  name = opts['patch_name'] or p.name
  q = repo.mq
  msg, user, date, diff = patch.parse(unicode(p.data,'utf-8'))
  if not msg:
    msg = p.commit_message
  if not user:
    username, useremail = p.attacher.who, p.attacher.who_email
    if username and useremail:
      user = "%s <%s>" % (cleanUserName(username), useremail)
  patchpath = q.join(name)
  # Newer versions of mercurial have promptchoice but the latest release (1.3.1) does not seem to
  prompter = ui.promptchoice if hasattr(ui, 'promptchoice') else ui.prompt
  try:
    while os.path.exists(patchpath):
      choice = prompter("The patch already seems to exist in your patch directory. Rename (r)/overwrite (o)/cancel (c)?",
                        choices = ("&readonly", "&overwrite", "&cancel"),
                        default='o')
      if choice == 'c':
        return
      elif choice == 'r':
        name = ui.prompt("Enter the new patch name (old one was %s):" % name)
        patchpath = q.join(name)
      else: # overwrite
        break;
  except KeyboardInterrupt:
    return

  try:
    sb = StringIO()
    sb.write(u'From: %s\n' % user)
    sb.write(msg + u'\n')
    sb.write(diff)
    sb.flush()

    patchcontents = sb.getvalue().encode('utf-8')

    # Invoke editor if need be
    if opts['preview']:
      patchcontents = ui.edit(patchcontents, ui.username())

    # Check if the patch is already in the queue
    if name in q.series:
      if q.isapplied(name):
        ui.warn("Patch was already applied. Changes will not take effect until the patch is reapplied.")

    # Write patch to disk and import
    if not opts['dry_run']:
      f = file(patchpath, 'wb')
      f.truncate(0)
      f.write(patchcontents)
      f.flush()
      f.close()
      # If we're not overwriting, inform mercurial of the new patch
      if not name in q.series:
        q.qimport(repo, [patchpath], patchname=name, existing=True, rev=[])
        q.save_dirty()
  except OSError, e:
    print e
    return

def qimportbz(ui, repo, *bugnums, **opts):
  """Imports a patch from a bug into the mercurial queue"""
  global hgui, hgopts
  hgui = ui
  hgopts = opts

  bzbase = ui.config('qimportbz', 'bugzilla',
                     os.environ.get('BUGZILLA',"bugzilla.mozilla.org"))
  for bugnum in bugnums:
    ui.status("Importing bug %s\n" % bugnum)
    bug = bz.Bug(bzbase, bugnum)
    patches = [patch for patch in bug.patches if not patch.obsolete]
    if len(patches) == 0:
      patches = bug.patches
      if len(patches) == 0:
        ui.warn("No patches found for this bug")
        continue
      elif len(patches) > 1:
        ui.warn("Only obsolete patches found")
      else:
        if 'y' != ui.prompt("Only found one patch and it is obsolete. Import anyways? (y/n)"):
          return
    if len(patches) == 1:
      importPatch(ui, repo, patches[0], opts)
    elif len(patches) > 0:
      for i,p in enumerate(patches):
        ui.write("%s: %s %s\n" % (i+1, p.desc, p.joinFlags()))
      choicestr = ui.prompt("Which patches do you want to import?", default="1")
      for choice in (s.strip() for t in choicestr.split(',') for s in t.split()):
        try:
          patch = patches[int(choice)-1]
        except (ValueError, IndexError):
          ui.warn("Invalid patch # %d" % choice)
          continue
        importPatch(ui, repo, patch, opts)

