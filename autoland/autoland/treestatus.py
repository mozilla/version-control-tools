import config
import requests

TREESTATUS_URL = 'https://treestatus.mozilla.org/'


def tree_is_open(tree):
    if config.testing():
        return True

    try:
        r = requests.get(TREESTATUS_URL + tree + '?format=json', verify=False)
        if r.status_code == 200:
            return r.json()['status'] == 'open'
    except (KeyError, requests.exceptions.ConnectionError):
        return False


if __name__ == '__main__':
    import sys
    print(tree_is_open(sys.argv[1]))
