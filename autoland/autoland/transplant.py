import io
import json
import logging
import re
import tempfile
import urlparse

import boto3
import hglib
import requests
from botocore.exceptions import ClientError

import config

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
        configs = ['ui.interactive=False', 'extensions.purge=']
        self.hg_repo = hglib.open(self.path, encoding='utf-8', configs=configs)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.clean_repo()
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

        # Strip any lingering changes.
        self.clean_repo()

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

    def clean_repo(self):
        # Strip any lingering draft changesets.
        try:
            self.run_hg(['strip', '--no-backup', '-r', 'not public()'])
        except hglib.error.CommandError:
            pass
        # Clean working directory.
        try:
            self.run_hg(['--quiet', 'revert', '--no-backup', '--all'])
        except hglib.error.CommandError:
            pass
        try:
            self.run_hg(['purge', '--all'])
        except hglib.error.CommandError:
            pass

    def dirty_files(self):
        return self.run_hg(['status', '--modified', '--added', '--removed',
                            '--deleted', '--unknown', '--ignored'])

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

        dirty_files = self.dirty_files()
        if dirty_files:
            logger.error('repo is not clean: %s' % ' '.join(dirty_files))
            raise Exception("We're sorry - something has gone wrong while "
                            "landing your commits. The repository contains "
                            "unexpected changes. "
                            "Please file a bug.")

        self.run_hg(['update', remote_tip])

        for patch_url in self.patch_urls:
            if patch_url.startswith('s3://'):
                # Download patch from s3 to a temp file.
                io_buf = self._download_from_s3(patch_url)

            else:
                # Download patch directly from url.  Using a temp file here
                # instead of passing the url to 'hg import' to make
                # testing's code path closer to production's.
                io_buf = self._download_from_url(patch_url)

            with tempfile.NamedTemporaryFile() as temp_file:
                temp_file.write(io_buf.getvalue())
                temp_file.flush()

                # Apply the patch, with file rename detection (similarity).
                # Using 95 as the similarity to match automv's default.
                logger.info(self.run_hg(['import', '-s', '95', temp_file.name]))

        return self.run_hg(['log', '-r', '.', '-T', '{node}'])

    @staticmethod
    def _download_from_s3(patch_url):
        # Download from s3 url specified in self.patch_url, returns io.BytesIO.
        url = urlparse.urlparse(patch_url)
        bucket = url.hostname
        key = url.path[1:]

        buckets_config = config.get('patch_url_buckets')
        if bucket not in buckets_config:
            logging.error('bucket "%s" not configured in patch_url_buckets'
                          % bucket)
            raise Exception('invalid patch_url')
        bucket_config = buckets_config[bucket]

        if ('aws_access_key_id' not in bucket_config or
                'aws_secret_access_key' not in bucket_config):
            logging.error('bucket "%s" is missing aws_access_key_id or '
                          'aws_secret_access_key' % bucket)
            raise Exception('invalid patch_url')

        try:
            s3 = boto3.client(
                's3',
                aws_access_key_id=bucket_config['aws_access_key_id'],
                aws_secret_access_key=bucket_config['aws_secret_access_key'])

            buf = io.BytesIO()
            s3.download_fileobj(bucket, key, buf)
            return buf
        except ClientError as e:
            error_code = int(e.response['Error']['Code'])
            if error_code == 404:
                raise Exception('unable to download %s: file not found'
                                % patch_url)
            if error_code == 403:
                raise Exception('unable to download %s: permission denied'
                                % patch_url)
            raise

    @staticmethod
    def _download_from_url(patch_url):
        # Download from patch_url, returns io.BytesIO.
        r = requests.get(patch_url, stream=True)
        r.raise_for_status()
        return io.BytesIO(r.content)
