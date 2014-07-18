# This software may be used and distributed according to the terms of the
# GNU General Public License version 2 or any later version.

import BaseHTTPServer
from SimpleHTTPServer import SimpleHTTPRequestHandler
import os
import sys

port = int(sys.argv[1])
httpd = BaseHTTPServer.HTTPServer(('', port), SimpleHTTPRequestHandler)
fh = open('listening', 'w')
fh.close()
httpd.handle_request()
os.unlink('listening')
