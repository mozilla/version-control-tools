import json
import requests

MERCURIAL_URL = 'http://hg.mozilla.org'

def get_pushlog(tree, rev):
    url = MERCURIAL_URL + '/' + tree + '/json-pushes?changeset=' + rev

    r = requests.get(url)
    if r.status_code == 200:
        return json.loads(r.text)

def get_raw_revision(tree, rev):
        url = MERCURIAL_URL + '/' + tree + '/raw-rev/' + rev
        r = requests.get(url)
        if r.status_code == 200:
            return r.text

def get_changesets(tree, pushlog):
    changesets = {}
    for key in pushlog:
        for changeset in pushlog[key]['changesets']:
            text = get_raw_revision(tree, changeset)
            changesets[changeset] = text
    return changesets
