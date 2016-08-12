import config
import hglib
import json
import os
import re
import tempfile

REPO_CONFIG = {}


def get_repo_path(tree):
    return config.get('repos').get(tree,
                                   os.path.join(os.path.sep, 'repos', tree))


def formulate_hg_error(cmd, output):
    # we want to strip out any sensitive --config options
    cmd = map(lambda x: x if not x.startswith('bugzilla') else 'xxx', cmd)
    return 'hg error in cmd: ' + ' '.join(cmd) + ': ' + output


def transplant(logger, tree, destination, rev, trysyntax=None,
               push_bookmark=False, commit_descriptions=None):
    """Transplant a specified revision and ancestors to the specified tree.

    If ``trysyntax`` is specified, a Try commit will be created using the
    syntax specified.
    """
    path = get_repo_path(tree)
    configs = ['ui.interactive=False']
    with hglib.open(path, encoding='utf-8', configs=configs) as client:
        return _transplant(logger, client, tree, destination, rev,
                           trysyntax=trysyntax, push_bookmark=push_bookmark,
                           commit_descriptions=commit_descriptions)


def _transplant(logger, client, tree, destination, rev, trysyntax=None,
                push_bookmark=False, commit_descriptions=None):
    landed = True
    result = ''

    def run_hg(args):
        out = hglib.util.BytesIO()
        out_channels = {b'o': out.write, b'e': out.write}
        ret = client.runcommand(args, {}, out_channels)

        if ret:
            raise hglib.error.CommandError(args, ret, out, None)

        return out.getvalue()

    # Obtain remote tip. We assume there is only a single head.
    # Output can contain bookmark or branch name after a space. Only take
    # first component.
    try:
        cmd = ['identify', 'upstream', '-r', 'tip']
        remote_tip = run_hg(cmd)
    except hglib.error.CommandError as e:
        return False, formulate_hg_error(['hg'] + cmd, '')
    remote_tip = remote_tip.split()[0]
    assert len(remote_tip) == 12, remote_tip

    # Strip any lingering draft changesets
    try:
        run_hg(['strip', '--no-backup', '-r', 'not public()'])
    except hglib.error.CommandError as e:
        pass

    # Pull "upstream" and update to remote tip. Pull revisions to land and
    # update to them.
    cmds = [['pull', 'upstream'],
            ['rebase', '--abort', '-r', remote_tip],
            ['update', '--clean', '-r', remote_tip],
            ['pull', tree, '-r', rev],
            ['update', rev]]

    for cmd in cmds:
        try:
            output = run_hg(cmd)
            if 'log' in cmd:
                result = output
        except hglib.error.CommandError as e:
            output = e.out.getvalue()
            if 'no changes found' in output:
                # we've already pulled this revision
                continue
            elif 'abort: no rebase in progress' in output:
                # there was no rebase in progress, nothing to see here
                continue
            else:
                output = e.out.getvalue()
                return False, formulate_hg_error(['hg'] + cmd, str(output))

    # If we are given commit_descriptions, we rewrite the commits based
    # upon this. We also determine the oldest commit that is part of the
    # commit descriptions and use this as the source revision when we we
    # rebase.
    base_revision = None
    if commit_descriptions:
        with tempfile.NamedTemporaryFile() as f:
            json.dump(commit_descriptions, f)
            f.flush()

            try:
                cmd = ['rewritecommitdescriptions',
                       '--descriptions=%s' % f.name, rev]
                cmd_output = run_hg(cmd)
            except hglib.error.CommandError as e:
                return False, formulate_hg_error(['hg'] + cmd, e.out.getvalue())

        for line in cmd_output.splitlines():
            m = re.search(r'^rev: [0-9a-z]+ -> ([0-9a-z]+)', line)
            if m and m.groups():
                base_revision = m.groups()[0]
                break

        if not base_revision:
            return False, ('Could not determine base revision for rebase: ' +
                           cmd_output)

        logger.info('base revision: %s' % base_revision)

    if not trysyntax and not base_revision:
        return False, 'Could not determine base revision for rebase'

    # Perform rebase if necessary
    if not trysyntax:
        try:
            run_hg(['rebase', '-s', base_revision, '-d', remote_tip])
        except hglib.error.CommandError as e:
            output = e.out.getvalue()
            if 'nothing to rebase' not in output:
                return False, formulate_hg_error(['hg'] + cmd, output)

        try:
            result = run_hg(['log', '-r', 'tip', '-T', '{node|short}'])
        except hglib.error.CommandError as e:
            output = e.out.getvalue()
            return False, formulate_hg_error(['hg'] + cmd, output)

        logger.info('rebased (tip) revision: %s' % result)

        # Match outgoing commit descriptions against incoming commit
        # descriptions. If these don't match exactly, prevent the landing
        # from occurring.
        incoming_descriptions = set([c.encode(client.encoding)
                                     for c in commit_descriptions.values()])
        outgoing = client.outgoing('tip', destination)
        outgoing_descriptions = set([commit[5] for commit in outgoing])

        if incoming_descriptions ^ outgoing_descriptions:
            logger.error('unexpected outgoing commits:')
            for commit in outgoing:
                logger.error('outgoing: %s: %s' % (commit[1], commit[5]))

            return False, ('We\'re sorry - something has gone wrong while '
                           'rewriting or rebasing your commits. The commits '
                           'being pushed no longer match what was requested. '
                           'Please file a bug.')

    # Now we push to the destination
    if trysyntax:
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
    elif push_bookmark:
        cmds = [['bookmark', push_bookmark],
                ['push', '-B', push_bookmark, destination]]
    else:
        cmds = [['push', '-r', 'tip', destination]]

    for cmd in cmds:
        try:
            output = run_hg(cmd)
            if 'log' in cmd:
                result = output
        except hglib.error.CommandError as e:
            output = e.out.getvalue()
            return False, formulate_hg_error(['hg'] + cmd, output)

    # Strip any lingering draft changesets
    try:
        run_hg(['strip', '--no-backup', '-r', 'not public()'])
    except hglib.error.CommandError as e:
        pass

    return landed, result
