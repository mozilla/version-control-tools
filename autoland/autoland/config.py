import json
import os
import re

CONFIG_PATH = os.path.join(os.path.dirname(os.path.realpath(__file__)),
                           'config.json')
CONFIG = None
LAST_MTIME = None


def get(key, default=None):
    global CONFIG
    global LAST_MTIME

    mtime = os.stat(CONFIG_PATH).st_mtime

    if CONFIG is None:
        with open(CONFIG_PATH) as f:
            CONFIG = json.load(f)
            LAST_MTIME = mtime
    elif mtime != LAST_MTIME:
        with open(CONFIG_PATH) as f:
            CONFIG = json.load(f)
            LAST_MTIME = mtime
    return CONFIG.get(key, default)


def get_repo(name):
    # Returns the configuration of a repository, containing the full path
    # to the repo, and the official name of the tree which can be fed into
    # treestatus.  'path' is guaranteed to be a path, 'tree' may be None.
    repos = get('repos', [])

    repo = {'path': None, 'tree': None}
    if name in repos:
        repo['path'] = repos[name].get('path')
        repo['tree'] = repos[name].get('tree')

    # Default to paths under /repos/
    if not repo['path']:
        repo['path'] = '/repos/%s' % name

    # Set treestatus name automatically for integration repos.
    if not repo['tree']:
        m = re.match('ssh://hg\.mozilla\.org/integration/([^/]+)', name)
        if m and m.groups():
            repo['tree'] = m.groups()[0]

    return repo


def testing():
    return get('testing', False)
