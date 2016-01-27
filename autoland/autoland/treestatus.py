import config
import re
import requests

TREESTATUS_URL = 'https://treestatus.mozilla.org/'


def tree_is_open(tree):
    treestatus_url = TREESTATUS_URL
    if config.testing():
        treestatus_url = 'http://treestatus/'

    # Map integration branches to their short form name
    m = re.match('ssh://hg\.mozilla\.org/integration/([^/]+)', tree)
    if m and m.groups():
        tree = m.groups()[0]

    try:
        r = requests.get(treestatus_url + tree + '?format=json', verify=False)
        if r.status_code == 200:
            return r.json()['status'] == 'open'
        elif r.status_code == 404:
            # We assume unrecognized trees are open
            return True
    except (KeyError, requests.exceptions.ConnectionError):
        return False


if __name__ == '__main__':
    import sys
    print(tree_is_open(sys.argv[1]))
