# This software may be used and distributed according to the terms of the
# GNU General Public License version 2 or any later version.

from __future__ import absolute_import

from ..checks import (
    ChangeGroupCheck,
    print_banner,
)

OUT_OF_DATE_CLIENT = """
YOU ARE PUSHING WITH AN OUT OF DATE MERCURIAL CLIENT!

Newer versions are faster and have numerous bug fixes.
Upgrade instructions are at the following URL:
https://mozilla-version-control-tools.readthedocs.io/en/latest/hgmozilla/installing.html
"""


class AdvertiseUpgradeCheck(ChangeGroupCheck):

    @property
    def name(self):
        return 'advertise_upgrade'

    def relevant(self):
        return True

    def check(self, **kwargs):
        if 'bundle2' not in kwargs:
            print_banner(self.ui, 'warning', OUT_OF_DATE_CLIENT)
        return True
