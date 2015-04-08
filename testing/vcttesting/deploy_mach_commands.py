# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from mach.decorators import (
    CommandArgument,
    CommandProvider,
    Command,
)

from vcttesting.deploy import deploy_reviewboard_dev


@CommandProvider
class DeployCommands(object):
    def __init__(self, context):
        lm = context.log_manager
        lm.enable_unstructured()

    @Command('reviewboard-dev', category='deploy',
             description='Deploy updates to the Review Board dev server')
    @CommandArgument('--repo',
                     help='Alternative repository URL to deploy from')
    @CommandArgument('--rev',
                     help='Explicit revision in repository to deploy from')
    @CommandArgument('--verbosity', type=int,
                     help='How verbose to be with output')
    def reviewboard_dev(self, repo=None, rev=None, verbosity=None):
        return deploy_reviewboard_dev(repo=repo, rev=rev, verbosity=verbosity)
