import os
import re
try:
  import cStringIO as StringIO
except ImportError:
  import StringIO
import subprocess
import sys
import tempfile
import urllib
import urllib2

def _relpath(filepath, start=os.curdir):
  """os.path.relpath is 2.6+, so don't rely on it being present.
See the os.path.relpath docs for further reference."""
  path, filename = os.path.split(filepath)
  pathdrive, path = os.path.splitdrive(os.path.abspath(path))
  startdrive, start = os.path.splitdrive(os.path.abspath(start))
  prefix = os.path.commonprefix((path, start))

  # interesting question: is it possible to construct a relative path
  # on windows that specifies a location on a drive different than the
  # drive in which the cwd is?
  assert pathdrive == startdrive

  def splitparts(p):  return filter(lambda s: s != '', p.split(os.sep))
  prefixlen = len(splitparts(prefix))
  pathparts = splitparts(path)[prefixlen:]
  startparts = splitparts(start)[prefixlen:]

  # walk from |start| to the LCA ...
  relpath = os.sep.join([ '..' ] * len(startparts))

  # then back down to |filepath|
  relpath = os.path.join(relpath, path)

  return os.path.join(relpath, filename)


class Handler(urllib2.BaseHandler):
  def __init__(self, ui, passmgr):
    self.ui = ui
    self.passmgr = passmgr
    self.scp = ui.config('qimportbz', 'scp', os.environ.get('SCP', "scp"))

  def scp_escape(self, path):
    return re.sub(r'(?<![\\])[ ]', '\\ ', path)

  def scp_open(self, req):
    scppath = self.scp_escape(
        urllib.unquote(req.get_full_url()[len('scp://'):]))

    _, tmpfilename = tempfile.mkstemp('.patch', 'qimportbz_scp')
    os.close(_)
    tmpfilename = self.scp_escape(tmpfilename)
    # Windows drive letters fool scp into thinking a path refers to a
    # remote machine in the mingw shell.  So instead, use a relative
    # path
    tmpfilename = _relpath(tmpfilename)

    output = ''
    try:
        if 0 != subprocess.call([ self.scp, scppath, tmpfilename ]):
            raise urllib2.URLError(
                "can't |scp '%s' '%s'|"% (scppath, tmpfilename))
        outf = open(tmpfilename)
        output = outf.read()
        outf.close()
    finally:
        os.remove(tmpfilename)

    return StringIO.StringIO(output)
