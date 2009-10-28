# std python modules
import urllib2
try:
  import cStringIO as StringIO
except ImportError:
  import StringIO
import os

# qimportbz modules
import bz

# Patch list
delayed_imports = []

# (Patch * path) list
imported_patches = []

class ObjectResponse(object):
  def __init__(self, obj):
    self.obj = obj
  def read(self):
    return self.obj

class Handler(urllib2.BaseHandler):
  def __init__(self, ui, passmgr):
    self.ui = ui
    self.passmgr = passmgr

    self.base = ui.config('qimportbz', 'bugzilla',
                          os.environ.get('BUGZILLA',"bugzilla.mozilla.org"))

  # Change the request to the https for the bug XML
  def bz_open(self, req):
    num = int(req.get_host())
    if num in bz.cache:
      bug = bz.cache[num]
      # strip the /
      attachid = req.get_selector()[1:]
      if attachid:
        return ObjectResponse(bug.get_patch(attachid))
      else:
        return ObjectResponse(bug)

    # Normal case, return a stream of text
    url = "https://%s/show_bug.cgi?ctype=xml&id=%s" % (self.base, num)
    self.ui.status("Fetching...")
    return self.parent.open(url)

  # Once the XML is fetched, parse and decide what to return
  def bz_response(self, req, res):
    patch = None
    # Check if we're doing a cached lookup - no ui in this case since we're
    # working around mq's limitations
    data = res.read()
    if isinstance(data, bz.Bug):
      bug = data
    elif isinstance(data, bz.Patch):
      patch = data
    else: # network read
      self.ui.status("done\n")
      self.ui.status("Parsing...")
      try:
        bug = bz.Bug(self.ui, data)
      # TODO: update syntax when mercurial requires Python 2.6
      except bz.PermissionError, e:
        self.ui.warn(e.msg + "\n")
        return
      self.ui.status("done\n")

    if not patch and req.get_selector():
      patch = bug.get_patch(req.get_selector())

    if not patch:
      patches = [p for p in bug.patches if not p.obsolete]
      if len(patches) == 0:
        patches = bug.patches
        if len(patches) == 0:
          self.ui.warn("No patches found for this bug\n")
          return
        elif len(patches) > 1:
          self.ui.warn("Only obsolete patches found\n")
        else:
          if 'y' != self.ui.prompt("Only found one patch and it is obsolete. Import anyways? (y/n)", default='y'):
            return
      if len(patches) == 1:
        patch = patches[0]
      elif len(patches) > 0:
        for i,p in enumerate(patches):
          self.ui.write("%s: %s %s\n" % (i+1, p.desc, p.joinFlags()))
        choicestr = self.ui.prompt("Which patches do you want to import?", default="1")
        for choice in (s.strip() for t in choicestr.split(',') for s in t.split()):
          try:
            p = patches[int(choice)-1]
          except (ValueError, IndexError):
            self.ui.warn("Invalid patch # %d\n" % choice)
            continue
          if not patch:
            patch = p
          else:
            delayed_imports.append(p)

    # and finally return the response
    if patch:
      imported_patches.append((patch, req.get_full_url()))
      return PatchResponse(patch)

# interface reverse engineered from urllib.addbase
class PatchResponse(object):
  def __init__(self, p):
    self.patch = p
    data = unicode(p)
    self.fp = fp = StringIO.StringIO(data.encode("utf-8"))
    self.read = fp.read
    self.readline = fp.readline
    self.close = fp.close

  def fileno(self):
    return None
