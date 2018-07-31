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

    @Command('mozreview-prod', category='deploy',
             description='Deploy MozReview to production')
    @CommandArgument('--repo',
                     help='Alternative repository URL to deploy from')
    @CommandArgument('--rev',
                     help='Explicit revision in repository to deploy from')
    @CommandArgument('--rb-repo',
                     help='Alternative reviewboard-fork repository URL to '
                          'deploy from')
    @CommandArgument('--rb-rev',
                     help='Explicit revision in the reviewboard-fork '
                          'repository to deploy from')
    @CommandArgument('--verbosity', type=int,
                     help='How verbose to be with output')
    def reviewboard_prod(self, repo=None, rev=None, rb_repo=None, rb_rev=None,
                         verbosity=None):
        from vcttesting.deploy import deploy_mozreview_prod
        return deploy_mozreview_prod(repo=repo, rev=rev, rb_repo=rb_repo,
                                     rb_rev=rb_rev, verbosity=verbosity)

    @Command('mozreview-create-repo', category='deploy',
             description='Create a new review repository')
    @CommandArgument('--verbosity', type=int,
                     help='How verbose to be with output')
    def mozreview_create_repo(self, verbosity=None):
        from vcttesting.deploy import mozreview_create_repo as deploy
        return deploy(verbosity=verbosity)

    @Command('github-webhooks', category='deploy',
             description='GitHub Web Hooks Lambda functions')
    def github_webhooks(self):
        from vcttesting.deploy import github_webhook_lambda

        github_webhook_lambda()

    @Command('hgmo', category='deploy',
             description='Deploy hg.mozilla.org')
    @CommandArgument('--verbosity', type=int,
                     help='How verbose to be with output')
    def hgmo(self, verbosity=None):
        from vcttesting.deploy import deploy_hgmo as deploy
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
    @CommandArgument('repo', nargs='*',
                     help='Repositories to re-clone')
    @CommandArgument('--repo-file',
                     help='File containing list of repositories to re-clone')
    def hgmo_reclone_repos(self, repo, repo_file=None):
        from vcttesting.deploy import hgmo_reclone_repos as reclone

        if repo_file:
            if repo:
                print('cannot specify repos from both arguments and a file')
                return 1

            repo = open(repo_file, 'rb').read().splitlines()

        return reclone(repo)

    @Command('reviewbot', category='deploy')
    @CommandArgument('--verbosity', type=int, default=0,
                     help='How verbose to be with output')
    def reviewbot(self, verbosity=0):
        from vcttesting.deploy import run_playbook

        return run_playbook('deploy-reviewbot', verbosity=verbosity)

    @Command('vcs-sync', category='deploy')
    @CommandArgument('--verbosity', type=int, default=0,
                     help='How verbose to be with output')
    def vcs_sync(self, verbosity=0):
        from vcttesting.deploy import deploy_vcs_sync

        return deploy_vcs_sync(verbosity=verbosity)
