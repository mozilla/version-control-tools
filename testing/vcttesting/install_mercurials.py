# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import os
import shutil
import subprocess
import sys

VERSIONS = [
    "6.7.4",
    "6.8.2",
    "6.9.5",
    "7.0.3",
    "7.1.2",
    "7.2.2",
]


def install_mercurials(venv_path):
    """Install supported Mercurial versions in isolated per-version venvs."""
    mercurials = os.path.join(venv_path, "mercurials")

    os.makedirs(mercurials, exist_ok=True)

    # Remove old versions.
    for entry in os.listdir(mercurials):
        if entry not in VERSIONS:
            print("removing old, unsupported Mercurial version: %s" % entry)
            shutil.rmtree(os.path.join(mercurials, entry))

    for version in VERSIONS:
        dest = os.path.join(mercurials, version)

        if os.path.exists(dest):
            continue

        print("installing Mercurial %s to %s" % (version, dest))
        subprocess.check_call(["uv", "venv", dest])
        subprocess.check_call(
            ["uv", "pip", "install", "--python", dest, "mercurial==%s" % version]
        )


if __name__ == "__main__":
    install_mercurials(
        venv_path=os.path.join("/app", "venv"),
    )
