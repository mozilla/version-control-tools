import json
import re
import subprocess

HGMO_REXP = 'https://hg.mozilla.org/try/rev/(\w+)'
REPO_CONFIG = {}


def transplant_to_try(tree, rev, trysyntax):

    """ This assumes that the repo has a bookmark for the head revision
        called 'central' and that the .hg/hgrc config contains links to
        the try and mozreview repos"""

    global REPO_CONFIG

    if not REPO_CONFIG:
        with open('config.json') as f:
            REPO_CONFIG = json.load(f)['repos']

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

    for cmd in cmds:
        try:
            repo_path = REPO_CONFIG.get(tree, '.')
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
