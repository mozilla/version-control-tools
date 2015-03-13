import os
import re
try:
    import cStringIO as StringIO
except ImportError:
    import StringIO
import subprocess
import tempfile
import urllib
import urllib2


class Handler(urllib2.BaseHandler):
    def __init__(self, ui, passmgr):
        self.ui = ui
        self.passmgr = passmgr
        self.scp = ui.config('qimportbz', 'scp', os.environ.get('SCP', "scp"))

    def scp_escape(self, path):
        return re.sub(r'(?<![\\])[ ]', '\\ ', path)

    def scp_open(self, req):
        scppath = self.scp_escape(urllib.unquote(req.get_full_url()[len('scp://'):]))

        _, tmpfilename = tempfile.mkstemp('.patch', 'qimportbz_scp')
        os.close(_)
        tmpfilename = self.scp_escape(tmpfilename)
        # Windows drive letters fool scp into thinking a path refers to a
        # remote machine in the mingw shell.  So instead, use a relative
        # path
        tmpfilename = os.path.relpath(tmpfilename)

        output = ''
        try:
            if 0 != subprocess.call([self.scp, scppath, tmpfilename]):
                raise urllib2.URLError("can't |scp '%s' '%s'|" % (scppath, tmpfilename))
            outf = open(tmpfilename)
            output = outf.read()
            outf.close()
        finally:
            os.remove(tmpfilename)

        return StringIO.StringIO(output)
