import config
import logging
import requests

TREESTATUS_URL = 'https://treestatus.mozilla-releng.net/trees/'

logger = logging.getLogger('autoland')


def tree_is_open(tree):
    # treestatus running in dev/CI is an older version, with slightly
    # different request and response structures.
    is_test_env = config.testing()

    r = None
    try:
        if is_test_env:
            r = requests.get('http://treestatus/%s?format=json' % tree)
        else:
            r = requests.get(TREESTATUS_URL + tree)

        if r.status_code == 200:
            if is_test_env:
                return r.json()['status'] == 'open'
            else:
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

