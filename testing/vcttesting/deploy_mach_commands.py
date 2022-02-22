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

    @Command('github-webhooks', category='deploy',
             description='GitHub Web Hooks Lambda functions')
    def github_webhooks(self):
        from vcttesting.deploy import github_webhook_lambda

        github_webhook_lambda()

    @Command('hgmo', category='deploy',
             description='Deploy hg.mozilla.org')
    @CommandArgument('--skip-hgssh', action='store_true',
                     help='Skip hgssh deployment if present')
    @CommandArgument('--skip-hgweb', action='store_true',
                     help='Skip hgweb deployment if present')
    @CommandArgument('--skip-mirrors', action='store_true',
                     help='Skip mirrors deployment if present')
    @CommandArgument('--clean-wdir', action='store_true',
                     help='Clean working directory of encrypted secrets '
                          'after deploy')
    @CommandArgument('--verbosity', type=int,
                     help='How verbose to be with output')
    def hgmo(self, skip_hgssh=False, skip_hgweb=False, skip_mirrors=False,
             clean_wdir=False, verbosity=None):
        from vcttesting.deploy import deploy_hgmo as deploy
        return deploy(
            clean_wdir=clean_wdir,
            skip_mirrors=skip_mirrors,
            skip_hgssh=skip_hgssh,
            skip_hgweb=skip_hgweb,
            verbosity=verbosity
        )

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

    @Command('hgweb-bootstrap', category='deploy',
             description='Bootstrap a new hgweb machine')
    @CommandArgument('--instance',
                     help='Instance type to bootstrap (hgweb, mirror or none)')
    @CommandArgument('--hgweb-workers', type=int,
                     help='Number of concurrent workers for hgweb bootstrap procedure')
    @CommandArgument('--hgssh-workers', type=int,
                     help='Number of concurrent workers for hgssh bootstrap procedure')
    @CommandArgument('--verbosity', type=int,
                     help='How verbose to be with output')
    def hgweb_bootstrap(self, instance=None, hgweb_workers=None, hgssh_workers=None,
                        verbosity=None):
        from vcttesting.deploy import run_playbook
        from vcttesting.vctutil import decrypt_sops_files

        decrypt_sops_files()

        # Create extra_vars dict using only non-`None` values
        # Ansible defaults only work if the value is undefined
        extra_vars = {
            key: val
            for key, val in {
                ('instance', instance),
                ('hgweb_workers', hgweb_workers),
                ('hgssh_workers', hgssh_workers),
            }
            if val is not None
        }

        return run_playbook('bootstrap-hgweb',
                            extra_vars=extra_vars,
                            verbosity=verbosity)

    @Command('reviewbot', category='deploy')
    @CommandArgument('--verbosity', type=int, default=0,
                     help='How verbose to be with output')
    def reviewbot(self, verbosity=0):
        from vcttesting.deploy import run_playbook

        return run_playbook('deploy-reviewbot', verbosity=verbosity)

