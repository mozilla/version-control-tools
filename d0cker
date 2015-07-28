#!/usr/bin/env python
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

# This script is used to manage Docker containers in the context of running
# Mercurial tests.

import os
import sys

from mach.main import Mach

def main(args):
    m = Mach(os.getcwd())
    m.define_category('docker', 'Docker',
        'Common actions involving Docker')
    import vcttesting.docker_mach_commands

    return m.run(args)

if __name__ == '__main__':
    # Unbuffer stdout.
    sys.stdout = os.fdopen(sys.stdout.fileno(), 'w', 0)

    sys.exit(main(sys.argv[1:]))
