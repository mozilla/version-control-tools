import config
import github
import json
import re
import subprocess
import tempfile

REVIEW_REXP = '^review url: (.+/r/\d+)'

REPO_CONFIG = {}


def get_repo_path(tree):
    return config.get('repos').get(tree, '.')


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
        return False, 'unknown tree: ' % tree

    # first purge any untracked files
    subprocess.call(['hg', 'purge', '--all'], cwd=repo_path)

    cmds = [['hg', 'update', '--clean', 'central'],
            ['hg', 'strip', '--no-backup', '-r', 'draft()'],
            ['hg', 'pull', 'default'],
            ['hg', 'update', 'central']]

    repo_path = get_repo_path(tree)

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
    cmds.append(['hg', 'update', 'central'])

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


def transplant_to_try(tree, rev, trysyntax):

    """ This assumes that the repo has a bookmark for the head revision
        called 'central' and that the .hg/hgrc config contains links to
        the try and mozreview repos"""

    landed = True
    result = ''

    cmds = [['hg', 'update', '--clean'],
            ['hg', 'update', 'central'],
            ['hg', 'pull', 'mozreview', '-r', rev],
            ['hg', 'bookmark', '-f', '-r', rev, 'transplant'],
            ['hg', 'update', 'transplant'],
            ['hg', 'qpop', '--all'],
            ['hg', 'qdelete', 'try'],
            # TODO: hg is going to add a ui.allowemptycommit flag in 3.5
            #       which means we can remove the use of queues here
            ['hg', 'qnew', 'try', '-m', '"' + trysyntax + '"'],
            ['hg', 'log', '-r', 'qtip', '-T', '{node|short}'],
            ['hg', 'push', '-r', '.', '-f', 'try'],
            ['hg', 'qpop'],
            ['hg', 'qdelete', 'try'],
            ['hg', 'strip', '--no-backup', '-r', 'draft()'],
            ['hg', 'update', 'central']]

    repo_path = get_repo_path(tree)
    qtip_rev = ''
    for cmd in cmds:
        try:
            output = subprocess.check_output(cmd, stderr=subprocess.STDOUT,
                                             cwd=repo_path)
            if 'log' in cmd:
                result = output
        except subprocess.CalledProcessError as e:
            # in normal circumstances we expect this mq error on delete
            if 'abort: patch try not in series' not in e.output:
                return False, formulate_hg_error(cmd, e.output)

    return landed, result
