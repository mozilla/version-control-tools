# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import BaseHTTPServer
import base64
import json
import os

RPM_DIR = '/hg-packages'

class RPMServer(BaseHTTPServer.BaseHTTPRequestHandler):
    def do_GET(self):
        result = {}

        for path in os.listdir(RPM_DIR):
            full = os.path.join(RPM_DIR, path)

            with open(full, 'rb') as fh:
                content = fh.read()

            result[path] = base64.b64encode(content)

        body = json.dumps(result)

        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', str(len(body)))
        self.wfile.write('\n')
        self.wfile.write(body)

if __name__ == '__main__':
    server = BaseHTTPServer.HTTPServer(('', 80), RPMServer)
    server.serve_forever()
