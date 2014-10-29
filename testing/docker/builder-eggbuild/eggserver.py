# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import BaseHTTPServer
import base64
import json
import os

EGG_DIRS = [
    '/version-control-tools/pylib/rbbz/dist',
    '/version-control-tools/pylib/rbmozui/dist',
]

def newest_egg(path):
    mtime = 0
    filename = None

    for f in os.listdir(path):
        full = os.path.join(path, f)
        m = os.path.getmtime(full)
        if m > mtime:
            m = mtime
            filename = full

    return filename

class EggServer(BaseHTTPServer.BaseHTTPRequestHandler):
    def do_GET(self):
        result = {}

        for d in EGG_DIRS:
            path = newest_egg(d)
            if not path:
                continue

            with open(path, 'rb') as fh:
                content = fh.read()

            result[os.path.basename(path)] = base64.b64encode(content)

        body = json.dumps(result)

        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', str(len(body)))
        self.wfile.write('\n')
        self.wfile.write(body)

if __name__ == '__main__':
    server = BaseHTTPServer.HTTPServer(('', 80), EggServer)
    server.serve_forever()
