import config
import hglib
import json
import logging
import os
import re
import tempfile

REPO_CONFIG = {}

logger = logging.getLogger('autoland')


class HgCommandError(Exception):
    def __init__(self, hg_args, out):
        # we want to strip out any sensitive --config options
        hg_args = map(lambda x: x if not x.startswith('bugzilla') else 'xxx',
                      hg_args)
        message = 'hg error in cmd: hg %s: %s' % (' '.join(hg_args),
                                                  out.getvalue())
        super(self.__class__, self).__init__(message)


def get_repo_path(tree):
    return config.get('repos').get(tree,
                                   os.path.join(os.path.sep, 'repos', tree))


def transplant(tree, destination, rev, trysyntax=None,
               push_bookmark=False, commit_descriptions=None):
    """Transplant a specified revision and ancestors to the specified tree.

    If ``trysyntax`` is specified, a Try commit will be created using the
    syntax specified.
    """
    # These values can appear in command arguments. Don't let unicode leak
    # into these.
    assert isinstance(tree, str)
    assert isinstance(destination, str)
    assert isinstance(rev, str)
    if push_bookmark:
        assert isinstance(push_bookmark, str)

    path = get_repo_path(tree)
    configs = ['ui.interactive=False']
    with hglib.open(path, encoding='utf-8', configs=configs) as hg_repo:
        tp = Transplant()
        return tp.transplant(hg_repo, tree, destination, rev,
                             trysyntax=trysyntax, push_bookmark=push_bookmark,
                             commit_descriptions=commit_descriptions)


class Transplant:
    def __init__(self):
        pass

    def transplant(self, hg_repo, tree, destination, rev, trysyntax=None,
                   push_bookmark=False, commit_descriptions=None):
        result = ''
        try:
            # Obtain remote tip. We assume there is only a single head.
            remote_tip = self.get_remote_tip(hg_repo, rev)

            # Strip any lingering draft changesets.
            self.strip_drafts(hg_repo, rev)

            # Pull from "upstream".
            self.update_repo(hg_repo, rev, tree, remote_tip)

            # Update commit descriptions and rebase.
            if not trysyntax:
                base_revision = self.rewrite_commit_descriptions(
                    hg_repo, rev, commit_descriptions)
                logger.info('base revision: %s' % base_revision)

                result = self.rebase(hg_repo, rev, base_revision, remote_tip)
                logger.info('rebased (tip) revision: %s' % result)

                self.validate_descriptions(hg_repo, destination,
                                           commit_descriptions)

            # Now we push to the destination
            if trysyntax:
                result = self.push_to_try(hg_repo, rev, trysyntax)
            elif push_bookmark:
                self.push_bookmark_to_repo(hg_repo, rev, destination,
                                           push_bookmark)
            else:
                self.push_to_repo(hg_repo, rev, destination)

            # Strip any lingering draft changesets.
            self.strip_drafts(hg_repo, rev)

            return True, result

        except Exception as e:
            return False, str(e)


    def run_hg(self, hg_repo, rev, args):
        logger.info('rev: %s: executing: %s' % (rev, args))
        out = hglib.util.BytesIO()
        out_channels = {b'o': out.write, b'e': out.write}
        ret = hg_repo.runcommand(args, {}, out_channels)
        if ret:
            raise hglib.error.CommandError(args, ret, out, None)
        return out.getvalue()


    def run_hg_cmds(self, hg_repo, rev, cmds):
        last_result = ''
        for cmd in cmds:
            try:
                last_result = self.run_hg(hg_repo, rev, cmd)
            except hglib.error.CommandError as e:
                raise HgCommandError(cmd, e.out)
        return last_result


    def strip_drafts(self, hg_repo, rev):
        # Strip any lingering draft changesets.
        try:
            self.run_hg(hg_repo, rev,
                        ['strip', '--no-backup', '-r', 'not public()'])
        except hglib.error.CommandError:
            pass


    def get_remote_tip(self, hg_repo, rev):
        # Obtain remote tip. We assume there is only a single head.
        # Output can contain bookmark or branch name after a space. Only take
        # first component.
        remote_tip = self.run_hg_cmds(hg_repo, rev, [
            ['identify', 'upstream', '-r', 'tip']
        ])
        remote_tip = remote_tip.split()[0]
        assert len(remote_tip) == 12, remote_tip
        return remote_tip


    def update_repo(self, hg_repo, rev, tree, remote_rev):
        # Pull "upstream" and update to remote tip. Pull revisions to land and
        # update to them.
        cmds = [['pull', 'upstream'],
                ['rebase', '--abort', '-r', remote_rev],
                ['update', '--clean', '-r', remote_rev],
                ['pull', tree, '-r', rev],
                ['update', rev]]

        for cmd in cmds:
            try:
                self.run_hg(hg_repo, rev, cmd)
            except hglib.error.CommandError as e:
                output = e.out.getvalue()
                if 'no changes found' in output:
                    # we've already pulled this revision
                    continue
                elif 'abort: no rebase in progress' in output:
                    # there was no rebase in progress, nothing to see here
                    continue
                else:
                    raise HgCommandError(cmd, e.out)


    def rewrite_commit_descriptions(self, hg_repo, rev, commit_descriptions):
        # Rewrite commit descriptions as per the mapping provided.  Returns the
        # revision of the base commit.
        assert commit_descriptions

        with tempfile.NamedTemporaryFile() as f:
            json.dump(commit_descriptions, f)
            f.flush()

            cmd_output = self.run_hg_cmds(hg_repo, rev, [
                ['rewritecommitdescriptions', '--descriptions=%s' % f.name, rev]
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


    def rebase(self, hg_repo, rev, base_revision, remote_tip):
        # Perform rebase if necessary.  Returns tip revision.
        cmd = ['rebase', '-s', base_revision, '-d', remote_tip]
        try:
            self.run_hg(hg_repo, rev, cmd)
        except hglib.error.CommandError as e:
            if 'nothing to rebase' not in e.out.getvalue():
                raise HgCommandError(cmd, e.out)

        return self.run_hg_cmds(hg_repo, rev, [
            ['log', '-r', 'tip', '-T', '{node|short}']
        ])


    def validate_descriptions(self, hg_repo, destination, commit_descriptions):
        # Match outgoing commit descriptions against incoming commit
        # descriptions. If these don't match exactly, prevent the landing
        # from occurring.
        incoming_descriptions = set([c.encode(hg_repo.encoding)
                                     for c in commit_descriptions.values()])
        outgoing = hg_repo.outgoing('tip', destination)
        outgoing_descriptions = set([commit[5] for commit in outgoing])

        if incoming_descriptions ^ outgoing_descriptions:
            logger.error('unexpected outgoing commits:')
            for commit in outgoing:
                logger.error('outgoing: %s: %s' % (commit[1], commit[5]))

            raise Exception("We're sorry - something has gone wrong while "
                            "rewriting or rebasing your commits. The commits "
                            "being pushed no longer match what was requested. "
                            "Please file a bug.")


    def push_to_try(self, hg_repo, rev, trysyntax):
        if not trysyntax.startswith("try: "):
            trysyntax = "try: %s" % trysyntax
        return self.run_hg_cmds(hg_repo, rev, [
            [
                '--encoding=utf-8',
                '--config', 'ui.allowemptycommit=true',
                'commit',
                '-m', trysyntax
            ],
            ['push', '-r', '.', '-f', 'try'],
            ['log', '-r', 'tip', '-T', '{node|short}'],
        ])


    def push_bookmark_to_repo(self, hg_repo, rev, destination, bookmark):
        self.run_hg_cmds(hg_repo, rev, [
            ['bookmark', bookmark],
            ['push', '-B', bookmark, destination],
        ])


    def push_to_repo(self, hg_repo, rev, destination):
        self.run_hg_cmds(hg_repo, rev, [
            ['push', '-r', 'tip', destination]
        ])

