# This software may be used and distributed according to the terms of the
# GNU General Public License version 2 or any later version.

from __future__ import absolute_import

import json

from mercurial import error

from ..checks import (
    PreTxnChangegroupCheck,
    print_banner,
)


REJECT_MESSAGE = b"""
Push contains unwanted changes to `.arcconfig` files.

Please ensure `.arcconfig` points to the Phab dev or stage servers for
`conduit-testing` repos.
"""

ARCCONFIG_PATH = b".arcconfig"

DEV_PHAB_URL = "https://phabricator-dev.allizom.org/"
STAGE_PHAB_URL = "https://phabricator.allizom.org/"


class PreventConduitArcconfig(PreTxnChangegroupCheck):
    """Prevent `.arcconfig` updates for `conduit-testing` repos."""

    @property
    def name(self):
        return b"prevent_conduit_arcconfig"

    def relevant(self) -> bool:
        return b"conduit-testing" in self.repo.root.split(b"/")

    def pre(self, _node):
        self.latest_arcconfig_contents = ""

    def check(self, ctx) -> bool:
        if ARCCONFIG_PATH in ctx.files():
            fctx = ctx[ARCCONFIG_PATH]
            self.latest_arcconfig_contents = fctx.data().decode("utf-8")

        return True

    def post_check(self) -> bool:
        if not self.latest_arcconfig_contents:
            # No updates to `.arcconfig`.
            return True

        try:
            arcconfig = json.loads(self.latest_arcconfig_contents)
        except json.JSONDecodeError as exc:
            raise error.Abort(b"Could not decode `.arcconfig` to JSON.") from exc

        if arcconfig["phabricator.uri"].startswith((DEV_PHAB_URL, STAGE_PHAB_URL)):
            # Latest state of `.arcconfig` maintains dev/stage URL.
            return True

        # `.arcconfig` has been updated to point to the wrong server (prod).
        print_banner(self.ui, b"error", REJECT_MESSAGE)
        return False
