import json
import requests

BUGZILLA_URL = 'https://bugzilla.mozilla.org'

def login():
    user, passwd = open('credentials/bugzilla.txt').read().strip().split(',')
    url = BUGZILLA_URL + '/rest/login?login=' + user + '&password=' + passwd
    try:
        r = requests.get(url)
        if r.status_code == 200:
            token = json.loads(r.text)['token']
            return token
    except requests.exceptions.ConnectionError:
        pass

def add_comment(token, bugid, comment):
    url = BUGZILLA_URL + '/rest/bug/' + bugid + '/comment' + '?token=' + token
    headers = {'Content-Type': 'application/json'}
    data = {
        'id': bugid,
        'comment': comment,
    }
    try:
        r = requests.post(url, data=data)
    except requests.exceptions.ConnectionError:
        return
    if r.status_code == 200:
        return r.text
