# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

"""Make the scripts in the parent directory importable by these tests."""

import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).parent.parent))
