# This software may be used and distributed according to the terms of the
# GNU General Public License version 2 or any later version.

from __future__ import absolute_import
from mozautomation.commitparser import (
    parse_requal_reviewers,
    is_backout,
)

from ..checks import (
    PreTxnChangegroupCheck,
    print_banner,
)

FTL_DRIVERS = [
    ("Francesco Lodolo", "flod"),
    ("Zibi Braniecki", "gandalf"),
    ("Axel Hecht", "pike"),
    ("Stas Malolepszy", "stas")
]


FTL_COMMIT_FOUND = """
You are trying to commit a change to an FTL file.
At the moment modifying FTL files requires a review from
one of the L10n Drivers.
Please, request review from either:
"""

for (name, nick) in FTL_DRIVERS:
    FTL_COMMIT_FOUND += "    - {} (:{})\n".format(name, nick)


class FTLCheck(PreTxnChangegroupCheck):
    """Prevents FTL file modifications without appropriate review.

    FTL is a new localization format currently being introduced
    into Gecko and Firefox.
    During the initial period we keep tight control over new
    FTL strings being added to the repository.

    In this period, we require that one of the L10n Drivers
    reviews every commit that touched an FTL file.
    """
    @property
    def name(self):
        return 'ftl_check'

    def relevant(self):
        return self.repo_metadata['firefox_releasing']

    def pre(self):
        pass

    def check(self, ctx):
        if len(ctx.parents()) > 1:
            # Skip merge changesets
            return True

        if is_backout(ctx.description()):
            # Ignore backouts
            return True

        if any(f.endswith('.ftl') for f in ctx.files()):
            requal = [
                r.lower() for r in parse_requal_reviewers(ctx.description())
            ]
            reviewers = [nick for (name, nick) in FTL_DRIVERS]
            if any(nick in reviewers for nick in requal):
                return True

            print_banner(self.ui, 'error', FTL_COMMIT_FOUND)
            return False
        return True

    def post_check(self):
        return True
