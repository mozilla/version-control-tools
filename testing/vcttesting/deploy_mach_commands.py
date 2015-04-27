# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from mach.decorators import (
    CommandArgument,
    CommandProvider,
    Command,
)


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
        from vcttesting.deploy import deploy_reviewboard_dev
        return deploy_reviewboard_dev(repo=repo, rev=rev, verbosity=verbosity)

    @Command('reviewboard-prod', category='deploy',
             description='Deploy Review Board to production')
    @CommandArgument('--repo',
                     help='Alternative repository URL to deploy from')
    @CommandArgument('--rev',
                     help='Explicit revision in repository to deploy from')
    @CommandArgument('--verbosity', type=int,
                     help='How verbose to be with output')
    def reviewboard_prod(self, repo=None, rev=None, verbosity=None):
        from vcttesting.deploy import deploy_reviewboard_prod
        return deploy_reviewboard_prod(repo=repo, rev=rev, verbosity=verbosity)

    @Command('hgmo-extensions', category='deploy',
             description='Deploy hooks and extensions to hg.mozilla.org')
    @CommandArgument('--verbosity', type=int,
                     help='How verbose to be with output')
    def hgmo_extensions(self, verbosity=None):
        from vcttesting.deploy import hgmo_deploy_extensions as deploy
        return deploy(verbosity=verbosity)

    @Command('hgmo-strip', category='deploy',
             description='Strip commits from a hg.mozilla.org repo')
    @CommandArgument('repo',
                     help='Repo to strip (path under hg.mozilla.org/)')
    @CommandArgument('rev',
                     help='Revset of revisions to strip')
    @CommandArgument('--verbosity', type=int,
                     help='How verbose to be with output')
    def hgmo_strip(self, repo, rev, verbosity=None):
        from vcttesting.deploy import hgmo_strip as strip
        return strip(repo, rev, verbosity=verbosity)

    @Command('hgmo-reclone-repos', category='deploy',
             description='Re-clone repositories on hg.mozilla.org')
    @CommandArgument('repo', nargs='+',
                     help='Repositories to re-clone')
    def hgmo_reclone_repos(self, repo):
        from vcttesting.deploy import hgmo_reclone_repos as reclone
        return reclone(repo)
