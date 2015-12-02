import config
import hglib
import json
import os
import re
import subprocess
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
               push_bookmark=False,
               commit_descriptions=None):
    """Transplant a specified revision and ancestors to the specified tree.

    If ``trysyntax`` is specified, a Try commit will be created using the
    syntax specified.
    """
    configs = ['ui.interactive=False']
    with hglib.open(get_repo_path(tree), configs=configs) as client:
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
                return False, formulate_hg_error(['hg'] + cmd, output)

    # If we are given commit_descriptions, we rewrite the commits based
    # upon this. We also determine the oldest commit that is part of the
    # commit descriptions and use this as the source revision when we we
    # rebase. This could push unreviewed commits if these were present
    # between reviewed commits but MozReview will create a review request
    # for every draft revision after a specified commit so this can not
    # (currently) happen.
    # TODO: we could run 'hg out' and ensure that every revision there
    #       is either present or was rewritten from a commit in
    #       commit_descriptions and refuse to land if that is not the case.
    base_revision = None
    if commit_descriptions:
        with tempfile.NamedTemporaryFile() as f:
            json.dump(commit_descriptions, f)
            f.flush()

            try:
                cmd = ['rewritecommitdescriptions',
                       '--descriptions=%s' % f.name, rev]
                base_revision = run_hg(cmd)
            except hglib.error.CommandError as e:
                return False, formulate_hg_error(['hg'] + cmd, base_revision)

        m = re.search(r'base: ([0-9a-z]+)$', base_revision)
        if not m or not m.groups():
            return False, ('Could not determine base revision for rebase: ' +
                           base_revision)

        base_revision = m.groups()[0]
        logger.info('base revision: %s' % base_revision)

    if not trysyntax and not base_revision:
        return False, 'Could not determine base revision for rebase'

    # Now we rebase (if necessary) and push to the destination
    if trysyntax:
        if not trysyntax.startswith("try: "):
            trysyntax =  "try: %s" % trysyntax

        cmds = [['--encoding=utf-8', '--config', 'ui.allowemptycommit=true', 'commit', '-m', trysyntax],
                ['log', '-r', 'tip', '-T', '{node|short}'],
                ['push', '-r', '.', '-f', 'try']]
    elif push_bookmark:
        # we assume use of the @ bookmark is mutually exclusive with using
        # try syntax for now.
        # We are updated to the head we are rebasing, so no need to specify
        # source or base revision.
        cmds = [['rebase', '-s', base_revision, '-d', remote_tip],
                ['log', '-r', 'tip', '-T', '{node|short}'],
                ['bookmark', push_bookmark],
                ['push', '-B', push_bookmark, destination]]
    else:
        cmds = [['rebase', '-s', base_revision, '-d', remote_tip],
                ['log', '-r', 'tip', '-T', '{node|short}'],
                ['push', '-r', 'tip', destination]]

    cmds.append(['strip', '--no-backup', '-r', 'not public()'])

    for cmd in cmds:
        try:
            output = run_hg(cmd)
            if 'log' in cmd:
                result = output
        except hglib.error.CommandError as e:
            output = e.out.getvalue()
            if 'nothing to rebase' in output:
                # we are already up to date so the rebase fails
                continue
            elif 'abort: empty revision set' in output:
                # no draft revisions so the strip fails
                continue
            else:
                return False, formulate_hg_error(['hg'] + cmd, output)

    return landed, result
