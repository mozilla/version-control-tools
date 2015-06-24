import json
import os

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


def testing():
    return get('testing', False)
