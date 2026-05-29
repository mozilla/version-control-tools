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


def install_mercurials(venv_path, venv_python, hg="hg"):
    """Install supported Mercurial versions in a central location."""
    hg_dir = os.path.join("/app", "venv", "hg")
    mercurials = os.path.join(venv_path, "mercurials")

    # Setting HGRCPATH to an empty value stops the global and user hgrc from
    # being loaded. These could interfere with behavior we expect from
    # vanilla Mercurial.
    hg_env = dict(os.environ)
    hg_env["HGRCPATH"] = ""

    # Ensure a Mercurial clone is present and up to date.
    if not os.path.isdir(hg_dir):
        print("cloning Mercurial repository to %s" % hg_dir)
        subprocess.check_call(
            [hg, "clone", "https://repo.mercurial-scm.org/hg", hg_dir],
            cwd="/",
            env=hg_env,
        )

    subprocess.check_call([hg, "pull"], cwd=hg_dir, env=hg_env)

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
        try:
            subprocess.check_output(
                [hg, "update", version],
                cwd=hg_dir,
                env=hg_env,
                stderr=subprocess.STDOUT,
            )
            # We don't care about support files, which only slow down
            # installation. So install-bin is a suitable target.
            subprocess.check_output(
                [
                    "make",
                    "install-bin",
                    "PREFIX=%s" % dest,
                    "PYTHON=%s" % venv_python,
                ],
                cwd=hg_dir,
                env=hg_env,
                stderr=subprocess.STDOUT,
            )
            subprocess.check_output(
                [hg, "--config", "extensions.purge=", "purge", "--all"],
                cwd=hg_dir,
                env=hg_env,
                stderr=subprocess.STDOUT,
            )
        except subprocess.CalledProcessError as error:
            print("error installing: %s" % error.output)
            raise Exception("could not install Mercurial")


if __name__ == "__main__":
    install_mercurials(
        venv_path=os.path.join("/app", "venv"),
        venv_python=os.path.join("/app", "venv", "bin", "python"),
    )
