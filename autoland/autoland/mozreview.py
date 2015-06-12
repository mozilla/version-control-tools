import json
import requests


def read_credentials():
    with open('config.json') as f:
        bugzilla = json.load(f)['bugzilla']
    return (bugzilla['user'], bugzilla['passwd'])


def update_review(auth, pingback_url, data):
    try:
        r = requests.post(pingback_url, data=data,
                          headers={'Content-Type': 'application/json'},
                          auth=auth)
        return r.status_code, r.text
    except requests.exceptions.ConnectionError:
        return None, 'could not connect'
