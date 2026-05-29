# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import os
import shutil
import subprocess
import sys

VERSIONS = [
    "6.1.4",
    "6.2.3",
    "6.3.2",
    "6.4.3",
    "6.5.2",
    "6.6.3",
    "6.7.4",
    "6.8.2",
    "6.9.5",
]


def install_mercurials(venv_path, venv_python):
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
        subprocess.check_call([venv_python, "-m", "venv", dest])
        subprocess.check_call(
            [os.path.join(dest, "bin", "pip"), "install", "mercurial==%s" % version]
        )


if __name__ == "__main__":
    install_mercurials(
        venv_path=os.path.join("/app", "venv"),
        venv_python=os.path.join("/app", "venv", "bin", "python"),
    )
