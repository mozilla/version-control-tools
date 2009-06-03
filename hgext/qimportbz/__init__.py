"""qimportbz

Imports patches from bugzilla to your mercurial queue

Configuration section is entirely optional but potentially useful.

[qimportbz]
bugzilla = server-address (defaults to BUGZILLA environment varable or bugzilla.mozilla.org)
joinstr = string to join flags for commit messages (default is ' ')
patch_format = Formatting string used to create patch names automatically
msg_format = Formatting string used to create commit messages automatically

Formatting strings are the standard python format strings where a dictionary is used to supply the data. Any % characters must be escaped since Python's configuration parser will try to interpret them. There are 5 pieces of patch metadata available for use:

      "bugnum" : the bug number
      "id" : the patch id (internal bugzilla number)
      "title" : the bug title
      "desc" : the patch description
      "flags" : all the flags

The default values are:
patch_format = bug-%(bugnum)s
msg_format = Bug %(bugnum)s - "%(title)s" [%(flags)s]
"""
from mercurial import util
import bz
from StringIO import StringIO
import patch
import os
import re

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
  try:
    while os.path.exists(patchpath):
      choice = ui.prompt("The patch already seems to exist in your patch directory. Rename (r)/overwrite (o)/cancel (c)?", pat = "r|o|c", default="o")
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
      return

    # Write patch to disk and import
    if not opts['dry_run']:
      f = file(patchpath, 'wb')
      f.truncate(0)
      f.write(sb.getvalue().encode('utf-8'))
      f.flush()
      f.close()
      q.qimport(repo, [patchpath], patchname=name, existing=True, rev=[])
      q.save_dirty()
  except OSError, e:
    print e
    return

def qimportbz(ui, repo, *bugnums, **opts):
  """Imports a patch from a bug into the mercurial queue"""
  bzbase = ui.config('qimportbz', 'bugzilla',
                     os.environ.get('BUGZILLA',"bugzilla.mozilla.org"))
  for bugnum in bugnums:
    ui.status("Importing bug %s\n" % bugnum)
    bug = bz.Bug(ui, bzbase, bugnum)
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
      choicestr = ui.prompt("Which patches do you want to import?", pat = '\d+((,\w*|\w+)\d+)*', default="1")
      for choice in (s.strip() for t in choicestr.split(',') for s in t.split()):
        try:
          patch = patches[int(choice)-1]
        except (ValueError, IndexError):
          ui.warn("Invalid patch # %d" % choice)
          continue
        importPatch(ui, repo, patch, opts)

cmdtable = {
  "qimportbz" : (qimportbz,
                 [('r', 'dry-run', False, "Perform a dry run - the patch queue will remain unchanged"),
                  ('p', 'preview', False, "Preview commit message"),
                  ('n', 'patch-name', '', "Override patch name")],
                 "hg qimportbz [-r] [-p] [-n NAME] BUG#")
}
