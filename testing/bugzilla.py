#!/usr/bin/env python
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

# This is a script for performing common Bugzilla operations from the command
# line. It is meant to support testing.

import os
import sys

from mach.main import Mach

HERE = os.path.abspath(os.path.dirname(__file__))
sys.path.insert(0, HERE)

def main(args):
    m = Mach(os.getcwd())
    m.define_category('bugzilla', 'Bugzilla',
        'Interface with Bugzilla', 50)
    import vcttesting.bugzilla.mach_commands

    return m.run(args)

if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
