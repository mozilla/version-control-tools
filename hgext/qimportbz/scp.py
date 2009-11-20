import os
import re
import subprocess
import tempfile
import urllib
import urllib2

class StringResponse(object):
  def __init__(self, s):
    self.string = s

  def read(self):
    return self.string

class Handler(urllib2.BaseHandler):
  def __init__(self, ui, passmgr):
    self.ui = ui
    self.passmgr = passmgr
    self.scp = ui.config('qimportbz', 'scp', os.environ.get('SCP', "scp"))

  def scp_escape(self, path):
    return re.sub(r'(?<![\\])[ ]', '\\ ', path)

  def scp_open(self, req):
    scppath = self.scp_escape(
        urllib.url2pathname(req.get_full_url()[len('scp://'):]))

    _, tmpfilename = tempfile.mkstemp('.patch', 'qimportbz_scp')

    output = ''
    try:
        if 0 != subprocess.call([ self.scp, scppath, tmpfilename ]):
            raise urllib2.URLError(
                "can't |scp '%s' '%s'|"% (scppath, tmpfilename))
        output = (open(tmpfilename)).read()
    finally:
        os.remove(tmpfilename)

    return StringResponse(output)
