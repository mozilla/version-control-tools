# std python modules
import urllib2
import os


class Handler(urllib2.BaseHandler):
    def __init__(self, ui, passmgr):
        self.ui = ui
        self.passmgr = passmgr

        self.base = ui.config('qimportbz', 'pastebin',
                              os.environ.get('PASTEBIN', "pastebin.mozilla.org"))

    # Change the request to the http to fetch the raw text
    def pb_open(self, req):
        url = "http://%s/?dl=%s" % (self.base, req.get_host())
        return self.parent.open(url)
