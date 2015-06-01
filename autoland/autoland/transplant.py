import github
import json
import re
import subprocess

REVIEW_REXP = '^review url: (.+/r/\d+)'

REPO_CONFIG = {}


def get_repo_path(tree):
    global REPO_CONFIG

    if not REPO_CONFIG:
        with open('config.json') as f:
            REPO_CONFIG = json.load(f)['repos']

    return REPO_CONFIG.get(tree, '.')


def transplant_to_mozreview(gh, tree, user, repo, pullrequest, bzuserid,
                            bzcookie, bugid):

    """For now, we assume the source for our request is a github pull request.
    """

    landed = False
    result = ''

    repo_path = get_repo_path(tree)
    if repo_path is None:
        return False, 'unknown tree: ' % tree

    cmds = [['hg', 'update', '--clean'],
            ['hg', 'strip', '--no-backup', '-r', 'draft()'],
            ['hg', 'pull'],
            ['hg', 'update', 'central'],
            ['hg', 'bookmark', '-f', 'transplant'],
            ['hg', 'update', 'transplant']]

    repo_path = get_repo_path(tree)

    commits = github.retrieve_commits(gh, user, repo, pullrequest, repo_path)
    if not commits:
        return False, 'no commits found!'

    for commit in commits:
        cmds.append(['hg', 'import', commit])
        cmds.append(['rm', commit])

    # actually push the revision and clean up
    cmds.append(['hg', '--config', 'bugzilla.userid=%s' % bzuserid,
                       '--config', 'bugzilla.cookie=%s' % bzcookie,
                       '--config', 'mozilla.ircnick=%s' % user,
                       'push', '--reviewid', str(bugid), '-r', 'transplant',
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
            if 'abort: empty revision set' not in e.output:
                result = e.output
                break

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
            #TODO: this should be logged, somewhere
            output = subprocess.check_output(cmd, stderr=subprocess.STDOUT,
                                             cwd=repo_path)
            if 'log' in cmd:
                result = output
        except subprocess.CalledProcessError as e:
            # in normal circumstances we expect this mq error on delete
            if 'abort: patch try not in series' not in e.output:
                landed = False
                result = e.output
                break

    return landed, result
