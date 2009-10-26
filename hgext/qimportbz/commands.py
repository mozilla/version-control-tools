from mercurial import util
import bz
from StringIO import StringIO
import os
import re

def importPatch(ui, repo, p, opts):
  name = opts['patch_name'] or p.name
  q = repo.mq
  patchpath = q.join(name)
  # Newer versions of mercurial have promptchoice but the latest release (1.3.1) does not seem to
  prompter = ui.promptchoice if hasattr(ui, 'promptchoice') else ui.prompt
  try:
    while os.path.exists(patchpath):
      prompt = "A patch for bug %d already seems to exist in your patch directory. Rename %s '%s' (%d) (r)/overwrite (o)/cancel (c)?" %
               (int(p.bug.num), 'patch' if isinstance(p, bz.Patch) else 'attachment', p.desc, int(p.id))
      choice = prompter(prompt,
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
