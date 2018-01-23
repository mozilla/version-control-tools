import logging
import os

import requests

import config

# treestatus running in dev/CI is an older version, with slightly
# different request and response structures.
TREESTATUS_PROD_URL = 'https://treestatus.mozilla-releng.net/trees/%s'
TREESTATUS_TEST_URL = 'http://treestatus/%s?format=json'

logger = logging.getLogger('autoland')


def tree_is_open(tree):
    treestatus_url = os.getenv(
        'TREESTATUS_URL', TREESTATUS_TEST_URL if config.testing()
        else TREESTATUS_PROD_URL)

    r = None
    try:
        r = requests.get(treestatus_url % tree)

        if r.status_code == 200:
            res = r.json()
            if 'result' in res:
                res = res['result']
            return res['status'] == 'open'

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

