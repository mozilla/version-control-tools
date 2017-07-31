import config
import hglib
import json
import logging
import re
import tempfile

REPO_CONFIG = {}

logger = logging.getLogger('autoland')


class HgCommandError(Exception):
    def __init__(self, hg_args, out):
        # we want to strip out any sensitive --config options
        hg_args = map(lambda x: x if not x.startswith('bugzilla') else 'xxx',
                      hg_args)
        message = 'hg error in cmd: hg %s: %s' % (' '.join(hg_args), out)
        super(self.__class__, self).__init__(message)


class Transplant(object):
    """Transplant a specified revision and ancestors to the specified tree."""

    def __init__(self, tree, destination, rev):
        # These values can appear in command arguments. Don't let unicode leak
        # into these.
        assert isinstance(tree, str), "tree arg is not str"
        assert isinstance(destination, str), "destination arg is not str"
        assert isinstance(rev, str), "rev arg is not str"

        self.tree = tree
        self.destination = destination
        self.source_rev = rev
        self.path = config.get_repo(tree)['path']

    def __enter__(self):
        configs = ['ui.interactive=False']
        self.hg_repo = hglib.open(self.path, encoding='utf-8', configs=configs)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.strip_drafts()
        self.hg_repo.close()

    def push_try(self, trysyntax):
        # Don't let unicode leak into command arguments.
        assert isinstance(trysyntax, str), "trysyntax arg is not str"

        remote_tip = self.update_repo()

        self.apply_changes(remote_tip)

        if not trysyntax.startswith("try: "):
            trysyntax = "try: %s" % trysyntax
        rev = self.run_hg_cmds([
            [
                '--encoding=utf-8',
                '--config', 'ui.allowemptycommit=true',
                'commit',
                '-m', trysyntax
            ],
            ['push', '-r', '.', '-f', 'try'],
            ['log', '-r', 'tip', '-T', '{node|short}'],
        ])

        return rev

    def push_bookmark(self, bookmark):
        # Don't let unicode leak into command arguments.
        assert isinstance(bookmark, str), "bookmark arg is not str"

        remote_tip = self.update_repo()

        rev = self.apply_changes(remote_tip)
        self.run_hg_cmds([
            ['bookmark', bookmark],
            ['push', '-B', bookmark, self.destination],
        ])

        return rev

    def push(self):
        remote_tip = self.update_repo()

        rev = self.apply_changes(remote_tip)
        self.run_hg_cmds([
            ['push', '-r', 'tip', self.destination]
        ])

        return rev

    def update_repo(self):
        # Obtain remote tip. We assume there is only a single head.
        remote_tip = self.get_remote_tip()

        # Strip any lingering draft changesets.
        self.strip_drafts()

        # Pull from "upstream".
        self.update_from_upstream(remote_tip)

        return remote_tip

    def apply_changes(self, remote_tip):
        raise NotImplemented('abstract method call: apply_changes')

    def run_hg(self, args):
        logger.info('rev: %s: executing: %s' % (self.source_rev, args))
        out = hglib.util.BytesIO()
        out_channels = {b'o': out.write, b'e': out.write}
        ret = self.hg_repo.runcommand(args, {}, out_channels)
        out = out.getvalue()
        if ret:
            if out:
                logging.error(out.rstrip())
            raise hglib.error.CommandError(args, ret, out, '')
        return out

    def run_hg_cmds(self, cmds):
        last_result = ''
        for cmd in cmds:
            try:
                last_result = self.run_hg(cmd)
            except hglib.error.CommandError as e:
                raise HgCommandError(cmd, e.out)
        return last_result

    def strip_drafts(self):
        # Strip any lingering draft changesets.
        try:
            self.run_hg(['strip', '--no-backup', '-r', 'not public()'])
        except hglib.error.CommandError:
            pass

    def get_remote_tip(self):
        # Obtain remote tip. We assume there is only a single head.
        # Output can contain bookmark or branch name after a space. Only take
        # first component.
        remote_tip = self.run_hg_cmds([
            ['identify', 'upstream', '-r', 'tip']
        ])
        remote_tip = remote_tip.split()[0]
        assert len(remote_tip) == 12, remote_tip
        return remote_tip

    def update_from_upstream(self, remote_rev):
        # Pull "upstream" and update to remote tip.
        cmds = [['pull', 'upstream'],
                ['rebase', '--abort', '-r', remote_rev],
                ['update', '--clean', '-r', remote_rev]]

        for cmd in cmds:
            try:
                self.run_hg(cmd)
            except hglib.error.CommandError as e:
                output = e.out
                if 'abort: no rebase in progress' in output:
                    # there was no rebase in progress, nothing to see here
                    continue
                else:
                    raise HgCommandError(cmd, e.out)

    def rebase(self, base_revision, remote_tip):
        # Perform rebase if necessary. Returns tip revision.
        cmd = ['rebase', '-s', base_revision, '-d', remote_tip]

        assert len(remote_tip) == 12

        # If rebasing onto the null revision, force the merge policy to take
        # our content, as there is no content in the destination to conflict
        # with us.
        if remote_tip == '0' * 12:
            cmd.extend(['--tool', ':other'])

        try:
            self.run_hg(cmd)
        except hglib.error.CommandError as e:
            if 'nothing to rebase' not in e.out:
                raise HgCommandError(cmd, e.out)

        return self.run_hg_cmds([
            ['log', '-r', 'tip', '-T', '{node|short}']
        ])


class RepoTransplant(Transplant):
    def __init__(self, tree, destination, rev, commit_descriptions):
        self.commit_descriptions = commit_descriptions

        super(RepoTransplant, self).__init__(tree, destination, rev)

    def apply_changes(self, remote_tip):
        # Pull in changes from the source repo.
        cmds = [['pull', self.tree, '-r', self.source_rev],
                ['update', self.source_rev]]
        for cmd in cmds:
            try:
                self.run_hg(cmd)
            except hglib.error.CommandError as e:
                output = e.out
                if 'no changes found' in output:
                    # we've already pulled this revision
                    continue
                else:
                    raise HgCommandError(cmd, e.out)

        # try runs don't have commit descriptions.
        if not self.commit_descriptions:
            return

        base_revision = self.rewrite_commit_descriptions()
        logger.info('base revision: %s' % base_revision)

        base_revision = self.rebase(base_revision, remote_tip)
        logger.info('rebased (tip) revision: %s' % base_revision)

        self.validate_descriptions()
        return base_revision

    def rewrite_commit_descriptions(self):
        # Rewrite commit descriptions as per the mapping provided.  Returns the
        # revision of the base commit.

        with tempfile.NamedTemporaryFile() as f:
            json.dump(self.commit_descriptions, f)
            f.flush()

            cmd_output = self.run_hg_cmds([
                ['rewritecommitdescriptions', '--descriptions=%s' % f.name,
                 self.source_rev]
            ])

            base_revision = None
            for line in cmd_output.splitlines():
                m = re.search(r'^rev: [0-9a-z]+ -> ([0-9a-z]+)', line)
                if m and m.groups():
                    base_revision = m.groups()[0]
                    break

            if not base_revision:
                raise Exception('Could not determine base revision for '
                                'rebase: %s' % cmd_output)

            return base_revision

    def validate_descriptions(self):
        # Match outgoing commit descriptions against incoming commit
        # descriptions. If these don't match exactly, prevent the landing
        # from occurring.
        incoming_descriptions = set(
            [c.encode(self.hg_repo.encoding)
             for c in self.commit_descriptions.values()])
        outgoing = self.hg_repo.outgoing('tip', self.destination)
        outgoing_descriptions = set([commit[5] for commit in outgoing])

        if incoming_descriptions ^ outgoing_descriptions:
            logger.error('unexpected outgoing commits:')
            for commit in outgoing:
                logger.error('outgoing: %s: %s' % (commit[1], commit[5]))

            raise Exception("We're sorry - something has gone wrong while "
                            "rewriting or rebasing your commits. The commits "
                            "being pushed no longer match what was requested. "
                            "Please file a bug.")


class PatchTransplant(Transplant):
    def __init__(self, tree, destination, rev, patch_urls):
        self.patch_urls = patch_urls

        super(PatchTransplant, self).__init__(tree, destination, rev)

    def apply_changes(self, remote_tip):
        assert self.patch_urls, 'patch_urls not provided'

        for patch_url in self.patch_urls:
            if patch_url.startswith('s3://'):
                # Download patch to temp file and import
                raise Exception('importing patches from s3 not implemented')

            else:
                self.run_hg(['update', remote_tip])
                output = self.run_hg(['import', patch_url])
                logger.info(output)
