# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

"""Run `replicatesync` on try to stay in sync.

A temporary band-aid solution while we investigate the recent
increase in frequency of this bug.
"""

import subprocess


def run_replicatesync():
    subprocess.check_output(
        ["/var/hg/venv_tools/bin/hg", "-R", "/repo/hg/mozilla/try", "replicatesync"]
    )


for attempt in range(3):
    try:
        run_replicatesync()
        print("`replicatesync` called successfully.")
        break
    except subprocess.CalledProcessError as exc:
        print(f"`replicatesync` failed on attempt {attempt}, trying again.")
        print(str(exc))
