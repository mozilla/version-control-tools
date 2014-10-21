# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import os
import sys

from mach.main import Mach

HERE = os.path.abspath(os.path.dirname(__file__))
ROOT = os.path.join(HERE, '..', '..', '..')
sys.path.insert(0, os.path.normpath(os.path.join(ROOT, 'testing')))

def main(args):
    m = Mach(os.getcwd())

    m.define_category('reviewboard', 'Review Board',
        'Interface with Review Board', 50)
    import vcttesting.reviewboard.mach_commands

    return m.run(args)

if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
