#!/var/hg/venv_pash/bin/python -u
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import json
import logging
import os
import sys
from datetime import datetime
from pathlib import Path

import hg_helper
from hgmolib import ldap_helper


AUTOLAND_USER = "bind-autoland@mozilla.com"
LANDING_WORKER_USER = "lando_landing_worker@mozilla.com"
LANDING_WORKER_USER_2 = "lando_landing_worker_2@mozilla.com"
LANDING_WORKER_USER_DEV = "lando_landing_worker_dev@mozilla.com"

PASH_JSON = Path("/etc/mercurial/pash.json")


def source_environment(path: Path):
    """Source a file with environment variables.

    Parsed environment variables are added to ``os.environ`` as a side-effect.
    """
    if not path.is_file():
        return

    # Open in text mode because environment variables are not bytes in Python
    # 3.
    with path.open("r") as fh:
        for line in fh:
            line = line.strip()

            if not line or line.startswith("#"):
                continue

            # Valid formats:
            # key=value
            # key="value"
            if "=" not in line:
                continue

            key, value = line.split("=", 1)

            key = key.strip()
            value = value.strip()

            if value.startswith('"') and value.endswith('"'):
                value = value[1:-1]

            os.environ[key] = value


def touch_hg_access_date(user):
    # Run ldap access date toucher, silently fail and log if we're unable to write
    try:
        settings = ldap_helper.get_ldap_settings()
        ldap_helper.update_access_date(
            user,
            "hgAccessDate",
            datetime.utcnow().strftime("%Y%m%d%H%M%S.%fZ"),
            settings["url"],
            settings["write_url"],
        )
    except Exception:
        logging.basicConfig(filename="/var/log/pash.log", level=logging.DEBUG)
        logging.exception("Failed to update LDAP attributes for %s" % user)


def process_login(user):
    try:
        # Validate user input.
        hg_helper.is_valid_user(user)
    except ValueError as err:
        sys.stderr.write(str(err))
        sys.exit(0)

    with PASH_JSON.open("rb") as fh:
        pash_settings = json.load(fh)

    touch_hg_access_date(user)

    # landing_users are both autoland-transplant and Lando landing worker
    # users that push on behalf of other users.
    landing_users = (
        pash_settings.get("autoland_user", AUTOLAND_USER),
        pash_settings.get("landing_worker_user", LANDING_WORKER_USER),
        pash_settings.get("landing_worker_user_2", LANDING_WORKER_USER_2),
        pash_settings.get("landing_worker_user_dev", LANDING_WORKER_USER_DEV),
    )

    # Touch the initiator of the autoland request, if required.
    if user in landing_users:
        request_user = os.environ.get("AUTOLAND_REQUEST_USER")
        if request_user:
            touch_hg_access_date(request_user)
    else:
        if "AUTOLAND_REQUEST_USER" in os.environ:
            del os.environ["AUTOLAND_REQUEST_USER"]

    hg_helper.serve(
        cname=pash_settings["hostname"],
        user=user,
        enable_repo_config=pash_settings.get("repo_config", False),
        enable_repo_group=pash_settings.get("repo_group", False),
        enable_user_repos=pash_settings.get("user_repos", False),
    )
    sys.exit(0)


if __name__ == "__main__":
    # /etc/environment contains important environment variables needed for
    # the execution of some functionality (like hooks making HTTP requests
    # and needing to pick up http_proxy and kin). This file is normally sourced
    # by login shells. But we are the login process and a shell is never
    # invoked. There are ways to get sshd to source a file with environment
    # variables by using PAM. But this feels  complicated and requires mucking
    # about with system auth settings. It is relatively easy to source the file
    # from Python. So we do that.
    source_environment(Path("/etc/environment"))

    process_login(os.environ.get("USER"))
