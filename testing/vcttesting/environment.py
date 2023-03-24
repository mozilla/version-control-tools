# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import errno
import os
import shutil
import subprocess
import sys


HERE = os.path.abspath(os.path.dirname(__file__))
ROOT = os.path.normpath(os.path.join(HERE, "..", ".."))
CREATE_VIRTUALENV = os.path.join(ROOT, "testing", "create-virtualenv")


SITECUSTOMIZE = b"""
import os

if os.environ.get('CODE_COVERAGE', False):
    import uuid
    import coverage

    covpath = os.path.join(os.environ['COVERAGE_DIR'], 'data',
                           'coverage.%s' % uuid.uuid1())
    cov = coverage.Coverage(data_file=covpath, auto_data=True, branch=True)
    cov._warn_no_data = False
    cov._warn_unimported_source = False
    cov.start()
"""


def create_virtualenv(name=None, python="python"):
    path = os.path.join(ROOT, "venv")

    env = dict(os.environ)
    env["PYTHON_VERSION"] = python

    if name:
        path = os.path.join(path, name)

    try:
        os.makedirs(os.path.dirname(path))
    except OSError as e:
        if e.errno != errno.EEXIST:
            raise

    if os.name == "nt":
        bin_dir = os.path.join(path, "Scripts")
        pip = os.path.join(bin_dir, "pip.exe")
        python = os.path.join(bin_dir, python + ".exe")
        activate = os.path.join(bin_dir, "activate")
    else:
        bin_dir = os.path.join(path, "bin")
        pip = os.path.join(bin_dir, "pip")
        python = os.path.join(bin_dir, python)
        activate = os.path.join(bin_dir, "activate")

    res = {
        "path": path,
        "bin_dir": bin_dir,
        "pip": pip,
        "python": python,
        "activate": activate,
        "activate_this": os.path.join(bin_dir, "activate_this.py"),
    }

    env["ROOT"] = ROOT
    env["VENV"] = path

    if not os.path.exists(res["pip"]):
        subprocess.check_call([CREATE_VIRTUALENV, path], env=env)

    # Install a sitecustomize.py that starts code coverage if an environment
    # variable is set.
    with open(os.path.join(bin_dir, "sitecustomize.py"), "wb") as fh:
        fh.write(SITECUSTOMIZE)

    return res


def activate_virtualenv(venv):
    """Activate a virtualenv in the current Python process."""
    with open(venv["activate_this"]) as f:
        exec(f.read(), dict(__file__=venv["activate_this"]))


def process_pip_requirements(venv, requirements):
    args = [
        venv["pip"],
        "install",
        "--upgrade",
        "--require-hashes",
        "-r",
        os.path.join(ROOT, requirements),
    ]

    hg_env = os.environ.copy()
    hg_env["HGPYTHON3"] = "1"

    subprocess.check_call(args, env=hg_env)


def install_editable(venv, relpath, extra_env=None):
    args = [
        venv["pip"],
        "install",
        "--no-deps",
        "--editable",
        os.path.join(ROOT, relpath),
    ]

    env = dict(os.environ)
    env.update(extra_env or {})

    subprocess.check_call(args, env=env)


def install_mercurials(venv, hg="hg"):
    """Install supported Mercurial versions in a central location."""
    VERSIONS = [
        "5.9.3",
        "6.0.3",
        "6.1.4",
        "6.2.3",
        "6.3.2",
        "6.4",
        "@",
    ]

    hg_dir = os.path.join("/app", "venv", "hg")
    mercurials = os.path.join(venv["path"], "mercurials")

    # Setting HGRCPATH to an empty value stops the global and user hgrc from
    # being loaded. These could interfere with behavior we expect from
    # vanilla Mercurial.
    hg_env = dict(os.environ)
    hg_env["HGRCPATH"] = ""
    hg_env["HGPYTHON3"] = "1"

    # Ensure a Mercurial clone is present and up to date.
    if not os.path.isdir(hg_dir):
        print("cloning Mercurial repository to %s" % hg_dir)
        subprocess.check_call(
            [hg, "clone", "https://www.mercurial-scm.org/repo/hg-committed", hg_dir],
            cwd="/",
            env=hg_env,
        )

    subprocess.check_call([hg, "pull"], cwd=hg_dir, env=hg_env)

    try:
        os.makedirs(mercurials)
    except OSError as e:
        if e.errno != errno.EEXIST:
            raise

    # Remove old versions.
    for p in os.listdir(mercurials):
        if p in (".", ".."):
            continue

        if p not in VERSIONS:
            print("removing old, unsupported Mercurial version: %s" % p)
            shutil.rmtree(os.path.join(mercurials, p))

    for v in VERSIONS:
        dest = os.path.join(mercurials, v)

        # Always reinstall @ because it isn't a static tag.
        if v == "@" and os.path.exists(dest):
            shutil.rmtree(dest)

        if os.path.exists(dest):
            continue

        print("installing Mercurial %s to %s" % (v, dest))
        try:
            subprocess.check_output(
                [hg, "update", v], cwd=hg_dir, env=hg_env, stderr=subprocess.STDOUT
            )
            # We don't care about support files, which only slow down
            # installation. So install-bin is a suitable target.
            subprocess.check_output(
                [
                    "make",
                    "install-bin",
                    "PREFIX=%s" % dest,
                    "PYTHON=%s" % venv["python"],
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
        except subprocess.CalledProcessError as e:
            print("error installing: %s" % e.output)
            raise Exception("could not install Mercurial")


def docker_client():
    """Attempt to obtain a Docker client.

    Returns a client on success. None on failure.
    """
    from .docker import (
        Docker,
        params_from_env,
    )

    docker_url, tls = params_from_env(os.environ)

    d = Docker(docker_url, tls=tls)

    return d if d.is_alive() else None


def create_docs():
    """Create environment used for building docs."""
    venv = create_virtualenv("docs")
    process_pip_requirements(venv, "docs-requirements.txt")

    install_editable(venv, "hghooks")
    install_editable(venv, "pylib/Bugsy")
    install_editable(venv, "pylib/mozhg")
    install_editable(venv, "pylib/mozhginfo")
    install_editable(venv, "pylib/mozautomation")
    install_editable(venv, "testing")

    return venv


def create_hgdev():
    """Create an environment used for hacking on Mercurial extensions."""
    venv = create_virtualenv("hgdev")
    reqs = "testing/requirements-hgdev.txt"

    process_pip_requirements(venv, reqs)
    install_editable(venv, "hghooks")
    install_editable(venv, "pylib/Bugsy")
    install_editable(venv, "pylib/mozhg")
    install_editable(venv, "pylib/mozhginfo")
    install_editable(venv, "pylib/mozautomation")
    install_editable(venv, "testing")

    install_mercurials(venv, hg=os.path.join(venv["bin_dir"], "hg"))

    return venv


def install_cinnabar(dest=None):
    """Install git-cinnabar"""
    if not dest:
        dest = os.path.join(ROOT, "venv", "git-cinnabar")

    if not os.path.exists(dest):
        subprocess.check_call(
            [
                "git",
                "clone",
                "--branch",
                "release",
                "https://github.com/glandium/git-cinnabar.git",
                dest,
            ]
        )

    subprocess.check_call(["git", "pull"], cwd=dest)

    subprocess.check_call(
        [
            "make",
            "-j4",
            "helper",
            "NO_OPENSSL=1",
            "NO_GETTEXT=1",
        ],
        cwd=dest,
    )


def create_global():
    """Create the global test environment virtualenv

    This functions the same as ./create-test-environment
    """
    from .hgmo import (
        HgCluster,
    )

    # No `name` parameter since this will be the top-level venv
    venv_py2 = create_virtualenv(python="python2")
    venv_py3 = create_virtualenv(name="py3", python="python3")

    venvs = (
        venv_py2,
        venv_py3,
    )

    # Install third-party dependencies
    process_pip_requirements(venv_py2, "test-requirements.txt")
    process_pip_requirements(venv_py3, "test-requirements-3.txt")

    # Install editable packages
    editables = {
        "hgserver/hgmolib",
        "pylib/Bugsy",
        "pylib/mozansible",
        "pylib/mozhg",
        "pylib/mozhginfo",
        "pylib/mozautomation",
        "pylib/vcsreplicator",
        "hghooks",
        "testing",
    }
    for venv in venvs:
        for package in editables:
            install_editable(venv, package)

    install_mercurials(venv_py2)
    install_mercurials(venv_py3)

    cinnabar_dest = os.path.join(venv_py2["path"], "git-cinnabar")
    install_cinnabar(dest=cinnabar_dest)

    if os.getenv("NO_DOCKER"):
        print("Not building Docker images because NO_DOCKER is set")
    else:
        print("Building Docker images.")
        print("This could take a while and may consume a lot of internet bandwidth.")
        print(
            "If you don't want Docker images, it is safe to hit CTRL+c to abort this."
        )

        try:
            HgCluster.build()
        except subprocess.CalledProcessError:
            print("You will not be able to run tests that require Docker.")
            print(
                "Please see https://docs.docker.com/installation/ for how to install Docker."
            )
            print("When Docker is installed, re-run this script")
            print(
                "To avoid re-building the Docker images next time, set the `NO_DOCKER` "
                "environment variable to any value."
            )
            sys.exit(1)

    # Return info about Py2 venv since we still require that to run tests
    return venv_py2


if __name__ == "__main__":
    import sys

    if sys.argv[1] != "install-mercurials":
        sys.exit(1)

    venv = {
        "path": os.path.join("/app", "venv"),
        "python": os.path.join("/app", "venv", "bin", "python"),
    }

    install_mercurials(venv, hg="hg")
    sys.exit(0)
