import github
import json
import re
import subprocess

HGMO_REXP = 'https://hg.mozilla.org/try/rev/(\w+)'
REVIEW_REXP = '^review url: .+/r/(\d+)'

REPO_CONFIG = {}


def get_repo_path(tree):
    global REPO_CONFIG

    if not REPO_CONFIG:
        with open('config.json') as f:
            REPO_CONFIG = json.load(f)['repos']

    return REPO_CONFIG.get(tree, '.')


def transplant_to_mozreview(tree, user, repo, pullrequest):

    """For now, we assume the source for our request is a github pull request.
    """

    landed = False
    result = ''

    cmds = [['hg', 'update', '--clean'],
            ['hg', 'update', 'central'],
            ['hg', 'bookmark', '-f', 'transplant'],
            ['hg', 'update', 'transplant']]

    repo_path = get_repo_path(tree)

    # create commands to import each github commit
    gh = github.connect()
    commits = github.retrieve_commits(gh, user, repo, pullrequest, repo_path)
    for commit in commits:
        cmds.append(['hg', 'import', commit])
        cmds.append(['rm', commit])

    # create commands to clean up
    commits.append(['hg', 'push', 'mozreview'])
    commits.append(['hg', 'update', 'central'])

    for cmd in cmds:
        try:
            output = subprocess.check_output(cmd, stderr=subprocess.STDOUT,
                                             cwd=repo_path)
            m = re.search(REVIEW_REXP, output)
            if m:
                landed = True
                result = m.groups()[0]
        except subprocess.CalledProcessError as e:
            result = e.output
            break

    return landed, result


def transplant_to_try(tree, rev, trysyntax):

    """ This assumes that the repo has a bookmark for the head revision
        called 'central' and that the .hg/hgrc config contains links to
        the try and mozreview repos"""

    landed = False
    result = ''

    cmds = [['hg', 'update', '--clean'],
            ['hg', 'update', 'central'],
            ['hg', 'pull', 'mozreview', '-r', rev],
            ['hg', 'bookmark', '-f', '-r', rev, 'transplant'],
            ['hg', 'update', 'transplant'],
            ['hg', 'qpop', '--all'],
            ['hg', 'qdelete', 'try'],
            ['hg', 'qnew', 'try'],
            ['hg', 'qrefresh', '-m', '"' + trysyntax + '"'],
            ['hg', 'push', '-r', '.', '-f', 'try'],
            ['hg', 'qpop'],
            ['hg', 'qdelete', 'try'],
            ['hg', 'update', 'central']]

    repo_path = get_repo_path(tree)
    for cmd in cmds:
        try:
            output = subprocess.check_output(cmd, stderr=subprocess.STDOUT,
                                             cwd=repo_path)
            m = re.search(HGMO_REXP, output)
            if m:
                landed = True
                result = m.groups()[0]
            #TODO: this should be logged, somewhere
        except subprocess.CalledProcessError as e:
            # in normal circumstances we expect this mq error on delete
            if 'abort: patch try not in series' not in e.output:
                result = e.output
                break

    return landed, result
