#!/usr/bin/env python
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import difflib
import json
import sys

with open(sys.argv[1], 'rb') as fh:
    a = json.load(fh)

with open(sys.argv[2], 'rb') as fh:
    b = json.load(fh)

if a == b:
    sys.exit(0)

alines = json.dumps(a, indent=2, sort_keys=True).splitlines()
blines = json.dumps(b, indent=2, sort_keys=True).splitlines()

diff = difflib.unified_diff(alines, blines, sys.argv[1], sys.argv[2], lineterm='')

for line in diff:
    print(line)

sys.exit(1)
