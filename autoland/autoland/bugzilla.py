import json
import requests

BUGZILLA_URL = 'https://bugzilla.mozilla.org'

def login():
    user, passwd = open('bugzilla-credentials.txt').read().strip().split(',')
    url = BUGZILLA_URL + '/rest/login?login=' + user + '&password=' + passwd
    r = requests.get(url)
    if r.status_code == 200:
        token = json.loads(r.text)['token']
        return token

def add_comment(token, bugid, comment):
    url = BUGZILLA_URL + '/rest/bug/' + bugid + '/comment' + '?token=' + token
    headers = {'Content-Type': 'application/json'}
    data = {
        'id': bugid,
        'comment': comment,
    }
    r = requests.post(url, data=data)
    return r.status_code, r.text
