import config
import hglib
import json
import logging
import os
import re
import tempfile

REPO_CONFIG = {}

logger = logging.getLogger('autoland')


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
        return _transplant(hg_repo, tree, destination, rev,
                           trysyntax=trysyntax, push_bookmark=push_bookmark,
                           commit_descriptions=commit_descriptions)


def _transplant(hg_repo, tree, destination, rev, trysyntax=None,
                push_bookmark=False, commit_descriptions=None):
    result = ''
    try:
        # Obtain remote tip. We assume there is only a single head.
        remote_tip = get_remote_tip(hg_repo, rev)

        # Strip any lingering draft changesets.
        strip_drafts(hg_repo, rev)

        # Pull from "upstream".
        update_repo(hg_repo, rev, tree, remote_tip)

        # Update commit descriptions and rebase.
        if not trysyntax:
            base_revision = rewrite_commit_descriptions(
                hg_repo, rev, commit_descriptions)
            logger.info('base revision: %s' % base_revision)

            result = rebase(hg_repo, rev, base_revision, remote_tip)
            logger.info('rebased (tip) revision: %s' % result)

            validate_descriptions(hg_repo, destination, commit_descriptions)

        # Now we push to the destination
        if trysyntax:
            result = push_to_try(hg_repo, rev, trysyntax)
        elif push_bookmark:
            push_bookmark_to_repo(hg_repo, rev, destination, push_bookmark)
        else:
            push_to_repo(hg_repo, rev, destination)

        # Strip any lingering draft changesets.
        strip_drafts(hg_repo, rev)

        return True, result

    except Exception as e:
        return False, str(e)


def get_repo_path(tree):
    return config.get('repos').get(tree,
                                   os.path.join(os.path.sep, 'repos', tree))


def formulate_hg_error(cmd, output):
    # we want to strip out any sensitive --config options
    cmd = map(lambda x: x if not x.startswith('bugzilla') else 'xxx', cmd)
    return 'hg error in cmd: ' + ' '.join(cmd) + ': ' + output


def run_hg(hg_repo, rev, args):
    logger.info('rev: %s: executing: %s' % (rev, args))
    out = hglib.util.BytesIO()
    out_channels = {b'o': out.write, b'e': out.write}
    ret = hg_repo.runcommand(args, {}, out_channels)
    if ret:
        raise hglib.error.CommandError(args, ret, out, None)
    return out.getvalue()


def strip_drafts(hg_repo, rev):
    # Strip any lingering draft changesets.
    try:
        run_hg(hg_repo, rev, ['strip', '--no-backup', '-r', 'not public()'])
    except hglib.error.CommandError:
        pass


def get_remote_tip(hg_repo, rev):
    # Obtain remote tip. We assume there is only a single head.
    # Output can contain bookmark or branch name after a space. Only take
    # first component.
    cmd = ['identify', 'upstream', '-r', 'tip']
    try:
        remote_tip = run_hg(hg_repo, rev, cmd)
    except hglib.error.CommandError:
        raise Exception(formulate_hg_error(['hg'] + cmd, ''))
    remote_tip = remote_tip.split()[0]
    assert len(remote_tip) == 12, remote_tip
    return remote_tip


def update_repo(hg_repo, rev, tree, remote_rev):
    # Pull "upstream" and update to remote tip. Pull revisions to land and
    # update to them.
    cmds = [['pull', 'upstream'],
            ['rebase', '--abort', '-r', remote_rev],
            ['update', '--clean', '-r', remote_rev],
            ['pull', tree, '-r', rev],
            ['update', rev]]

    for cmd in cmds:
        try:
            run_hg(hg_repo, rev, cmd)
        except hglib.error.CommandError as e:
            output = e.out.getvalue()
            if 'no changes found' in output:
                # we've already pulled this revision
                continue
            elif 'abort: no rebase in progress' in output:
                # there was no rebase in progress, nothing to see here
                continue
            else:
                raise Exception(formulate_hg_error(['hg'] + cmd,
                                                   e.out.getvalue()))


def rewrite_commit_descriptions(hg_repo, rev, commit_descriptions):
    # Rewrite commit descriptions as per the mapping provided.  Returns the
    # revision of the base commit.
    assert commit_descriptions, 'commit_descriptions requires for transplant'

    with tempfile.NamedTemporaryFile() as f:
        json.dump(commit_descriptions, f)
        f.flush()

        cmd = ['rewritecommitdescriptions', '--descriptions=%s' % f.name, rev]
        try:
            cmd_output = run_hg(hg_repo, rev, cmd)

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
        except hglib.error.CommandError as e:
            raise Exception(formulate_hg_error(['hg'] + cmd, e.out.getvalue()))


def rebase(hg_repo, rev, base_revision, remote_tip):
    # Perform rebase if necessary.  Returns tip revision.
    cmd = ['rebase', '-s', base_revision, '-d', remote_tip]
    try:
        run_hg(hg_repo, rev, cmd)
    except hglib.error.CommandError as e:
        output = e.out.getvalue()
        if 'nothing to rebase' not in output:
            raise Exception(formulate_hg_error(['hg'] + cmd, output))

    cmd = ['log', '-r', 'tip', '-T', '{node|short}']
    try:
        return run_hg(hg_repo, rev, cmd)
    except hglib.error.CommandError as e:
        raise Exception(formulate_hg_error(['hg'] + cmd, e.out.getvalue()))


def validate_descriptions(hg_repo, destination, commit_descriptions):
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


def push_to_try(hg_repo, rev, trysyntax):
    if not trysyntax.startswith("try: "):
        trysyntax = "try: %s" % trysyntax
    cmds = [
        [
            '--encoding=utf-8',
            '--config', 'ui.allowemptycommit=true',
            'commit',
            '-m', trysyntax
        ],
        ['log', '-r', 'tip', '-T', '{node|short}'],
        ['push', '-r', '.', '-f', 'try']
    ]

    result = ''
    for cmd in cmds:
        try:
            output = run_hg(hg_repo, rev, cmd)
            if 'log' in cmd:
                result = output
        except hglib.error.CommandError as e:
            raise Exception(formulate_hg_error(['hg'] + cmd, e.out.getvalue()))
    return result


def push_bookmark_to_repo(hg_repo, rev, destination, bookmark):
    cmds = [['bookmark', bookmark],
            ['push', '-B', bookmark, destination]]

    for cmd in cmds:
        try:
            run_hg(hg_repo, rev, cmd)
        except hglib.error.CommandError as e:
            raise Exception(formulate_hg_error(['hg'] + cmd, e.out.getvalue()))


def push_to_repo(hg_repo, rev, destination):
    cmds = [['push', '-r', 'tip', destination]]

    for cmd in cmds:
        try:
            run_hg(hg_repo, rev, cmd)
        except hglib.error.CommandError as e:
            raise Exception(formulate_hg_error(['hg'] + cmd, e.out.getvalue()))
