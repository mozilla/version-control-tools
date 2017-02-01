import config
import re
import requests

TREESTATUS_URL = 'https://treestatus.mozilla-releng.net/trees/'


def tree_is_open(logger, tree):
    treestatus_url = TREESTATUS_URL
    if config.testing():
        treestatus_url = 'http://treestatus/'

    # Map integration branches to their short form name
    m = re.match('ssh://hg\.mozilla\.org/integration/([^/]+)', tree)
    if m and m.groups():
        tree = m.groups()[0]

    r = None
    try:
        r = requests.get(treestatus_url + tree, verify=False)
        if r.status_code == 200:
            return r.json()['result']['status'] == 'open'
        elif r.status_code == 404:
            # We assume unrecognized trees are open
            return True
        else:
            logger.error('Unexpected response from treestatus API '
                         'for tree "%s": %s' % (tree, r.status_code))
    except KeyError:
        logger.error('Malformed response from treestatus API '
                     'for tree "%s"' % tree)
        if r is not None:
            logger.debug(r.json())
    except Exception as e:
        logger.error('Failed to determine treestatus for %s: %s' % (tree, e))

    return False


if __name__ == '__main__':
    import sys
    print(tree_is_open(sys.argv[1]))
