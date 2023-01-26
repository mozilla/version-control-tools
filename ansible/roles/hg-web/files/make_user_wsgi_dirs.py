#!/usr/bin/env python3
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import os
import pathlib

ROOT = "/repo/hg/mozilla/users"
WSGI_ROOT = "/repo/hg/webroot_wsgi/users"
BASE_URL = b"https://hg.mozilla.org/users"

CONFIG_TEMPLATE = """
[web]
baseurl = https://hg.mozilla.org/users/{user}
[paths]
/ = /repo/hg/mozilla/users/{user}/*
"""

WSGI_TEMPLATE = """
#!/usr/bin/env python
# This software may be used and distributed according to the terms of the
# GNU General Public License version 2 or any later version.

import os

OUR_DIR = os.path.normpath(os.path.dirname(__file__))
with open(os.path.join(OUR_DIR, '..', '..', 'bootstrap.py')) as f:
    exec(f.read())

application = make_application(OUR_DIR)
"""


for f in sorted(os.listdir(ROOT)):
    full = pathlib.Path(ROOT) / f

    if not full.is_dir():
        continue

    user = f

    wsgi_full = pathlib.Path(WSGI_ROOT) / user
    wsgi_full.mkdir(parents=True, exist_ok=True)

    config = wsgi_full / "hgweb.config"
    config_tmp = wsgi_full / "hgweb.config.tmp"
    wsgi = wsgi_full / "hgweb.wsgi"
    wsgi_tmp = wsgi_full / "hgweb.wsgi.tmp"

    with config_tmp.open("w", encoding="utf-8") as fh:
        fh.write(CONFIG_TEMPLATE.lstrip().format(user=user))

    config_tmp.rename(config)

    with wsgi_tmp.open("w", encoding="utf-8") as fh:
        fh.write(WSGI_TEMPLATE.lstrip())

    wsgi_tmp.rename(wsgi)
