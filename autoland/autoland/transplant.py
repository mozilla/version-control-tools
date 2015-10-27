import config
import github
import hglib
import json
import os
import re
import subprocess
import tempfile

REVIEW_REXP = '^review url: (.+/r/\d+)'

REPO_CONFIG = {}


def get_repo_path(tree):
    return config.get('repos').get(tree,
                                   os.path.join(os.path.sep, 'repos', tree))


def formulate_hg_error(cmd, output):
    # we want to strip out any sensitive --config options
    cmd = map(lambda x: x if not x.startswith('bugzilla') else 'xxx', cmd)
    return 'hg error in cmd: ' + ' '.join(cmd) + ': ' + output


def transplant_to_mozreview(gh, tree, user, repo, pullrequest, bzuserid,
                            bzcookie, bugid):
    """This transplants a github pullrequest to a mozreview repository. To
       keep things simple, we fold the git commits into a single commit
       prior to pushing."""

    landed = False
    result = ''

    repo_path = get_repo_path(tree)
    if repo_path is None:
        return False, 'unknown tree: %s' % tree

    if not os.path.isdir(repo_path):
        return False, 'bad repository path: %s for tree: %s' % (repo_path,
                                                                tree)

    # first purge any untracked files
    subprocess.call(['hg', 'purge', '--all'], cwd=repo_path)

    cmds = [['hg', 'update', '--clean'],
            ['hg', 'strip', '--no-backup', '-r', 'draft()'],
            ['hg', 'pull', 'upstream'],
            ['hg', 'update', 'upstream']]

    commits = github.retrieve_commits(gh, user, repo, pullrequest, repo_path)
    if not commits:
        return False, 'no commits found!'

    for commit in commits:
        cmds.append(['hg', 'import', commit])
        cmds.append(['rm', commit])

    # Run the commands to import from Github. We need to run these commands
    # separately so we can extract commit messages when we fold.
    for cmd in cmds:
        try:
            output = subprocess.check_output(cmd, stderr=subprocess.STDOUT,
                                             cwd=repo_path)
            m = re.search(REVIEW_REXP, output, re.MULTILINE)
            if m:
                landed = True
                result = m.groups()[0]
        except subprocess.CalledProcessError as e:
            # we might not actually strip anything in our initial cleanup
            if 'abort: empty revision set' not in e.output:
                return False, formulate_hg_error(cmd, e.output)
    cmds = []

    # we squash all of the commits together so we don't have to worry about
    # history editing on the git side for now.
    descf = None
    if len(commits) > 1:
        descf = tempfile.NamedTemporaryFile()
        try:
            cmd = ['hg', 'log', '-r', '::. and draft()', '-T', '{desc}\n']
            desc = subprocess.check_output(cmd, stderr=subprocess.STDOUT,
                                           cwd=repo_path)
            # if we don't get a description, our fold below will hang
            # indefinitely waiting for a user provided description
            if not desc:
                desc = 'folded commits for review'
            descf.write(desc)
        except subprocess.CalledProcessError as e:
            descf.close()
            return False, formulate_hg_error(cmd, e.output)

        # Using this name to open the temporarily file only works on unix like
        # systems. Happily we only run Autoland on unix like systems.
        cmds.append(['hg', 'fold', '-r', '::. and draft()', '-l', descf.name])

    # actually push the revision and clean up
    cmds.append(['hg', '--config', 'bugzilla.userid=%s' % bzuserid,
                       '--config', 'bugzilla.cookie=%s' % bzcookie,
                       '--config', 'mozilla.ircnick=%s' % user,
                       'push', '--reviewid', str(bugid), '-c', '.',
                       'mozreview-push'])
    cmds.append(['hg', 'strip', '--no-backup', '-r', 'draft()'])
    cmds.append(['hg', 'update', 'upstream'])

    for cmd in cmds:
        try:
            output = subprocess.check_output(cmd, stderr=subprocess.STDOUT,
                                             cwd=repo_path)
            m = re.search(REVIEW_REXP, output, re.MULTILINE)
            if m:
                landed = True
                result = m.groups()[0]
        except subprocess.CalledProcessError as e:
            if descf:
                descf.close()
            return False, formulate_hg_error(cmd, e.output)

    if descf:
        descf.close()

    return landed, result


def transplant(tree, destination, rev, trysyntax=None, push_bookmark=False,
               commit_descriptions=None):
    """Transplant a specified revision and ancestors to the specified tree.

    If ``trysyntax`` is specified, a Try commit will be created using the
    syntax specified.
    """
    with hglib.open(get_repo_path(tree)) as client:
        return _transplant(client, tree, destination, rev, trysyntax=trysyntax,
                           push_bookmark=push_bookmark,
                           commit_descriptions=commit_descriptions)

def _transplant(client, tree, destination, rev, trysyntax=None,
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
        cmd = ['identify', 'upstream']
        remote_tip = run_hg(cmd)
    except hglib.error.CommandError as e:
        return False, formulate_hg_error(['hg'] + cmd, '')
    remote_tip = remote_tip.split()[0]
    assert len(remote_tip) == 12, remote_tip

    cmds = [['rebase', '--abort'],
            ['update', '--clean'],
            ['pull', 'upstream'],
            ['update', remote_tip],
            ['pull', tree, '-r', rev],
            ['update', rev]]

    commit_descriptions_file = None
    if commit_descriptions:
        commit_descriptions_file = tempfile.NamedTemporaryFile()
        json.dump(commit_descriptions, commit_descriptions_file)
        commit_descriptions_file.flush()
        cmds.append(['rewritecommitdescriptions',
                     '--descriptions=%s' % commit_descriptions_file.name, rev])

    if trysyntax:
        if not trysyntax.startswith("try: "):
            trysyntax =  "try: %s" % trysyntax

        cmds.extend([['--config', 'ui.allowemptycommit=true', 'commit', '-m', trysyntax],
                     ['log', '-r', 'tip', '-T', '{node|short}'],
                     ['push', '-r', '.', '-f', 'try'],
                     ['strip', '--no-backup', '-r', 'draft()'],])
    elif push_bookmark:
        # we assume use of the @ bookmark is mutually exclusive with using
        # try syntax for now.
        # We are updated to the head we are rebasing, so no need to specify
        # source or base revision.
        cmds.extend([['rebase', '-d', remote_tip],
                     ['log', '-r', 'tip', '-T', '{node|short}'],
                     ['bookmark', push_bookmark],
                     ['push', '-B', push_bookmark, destination]])
    else:
        cmds.extend([['rebase', '-d', remote_tip],
                     ['log', '-r', 'tip', '-T', '{node|short}'],
                     ['push', '-r', 'tip', destination]])

    for cmd in cmds:
        try:
            output = run_hg(cmd)
            if 'log' in cmd:
                result = output
        except hglib.error.CommandError as e:
            output = e.out.getvalue()
            if 'abort: patch try not in series' in output:
                # in normal circumstances we expect this mq error on delete
                continue
            elif 'no changes found' in output:
                # we've already pulled this revision
                continue
            elif 'nothing to rebase' in output:
                # we are already up to date so the rebase fails
                continue
            elif 'abort: no rebase in progress' in output:
                # there was no rebase in progress, nothing to see here
                continue
            else:
                if commit_descriptions_file:
                    commit_descriptions_file.close()

                return False, formulate_hg_error(['hg'] + cmd, output)

    if commit_descriptions_file:
        commit_descriptions_file.close()

    return landed, result
