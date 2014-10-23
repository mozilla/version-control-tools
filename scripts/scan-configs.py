#!/usr/bin/env python
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

# This script scans the configs of Mercurial repositories from paths on stdin
# and prints a summary of the findings in JSON format.
#
# This script is useful for seeing what repositories use which hooks, etc.

import ConfigParser
import json
import os
import sys

options = {}

for path in sys.stdin:
    path = path.strip()

    hgrc = os.path.join(path, '.hg', 'hgrc')
    if not os.path.exists(hgrc):
        continue

    c = ConfigParser.ConfigParser()
    c.read([hgrc])

    for s in sorted(c.sections()):
        for k, v in c.items(s):
            options.setdefault(s, {}).setdefault(k, {}).setdefault(v, set()).add(path)

for section, keys in options.items():
    for key, values in keys.items():
        for value, s in values.items():
            options[section][key][value] = sorted(s)

print(json.dumps(options, indent=2, sort_keys=True))
