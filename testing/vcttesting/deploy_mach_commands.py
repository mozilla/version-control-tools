# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from mach.decorators import (
    CommandProvider,
    Command,
)

from vcttesting.deploy import run_playbook


@CommandProvider
class DeployCommands(object):
    @Command('reviewboard-dev', category='deploy',
             description='Deploy updates to the Review Board dev server')
    def reviewboard_dev(self):
        return run_playbook('reviewboard-dev')
