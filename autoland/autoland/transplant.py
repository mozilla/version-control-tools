import json
import requests

TRANSPLANT_URL = 'http://localhost:5000'

def transplant(src, dest, changesets):
    """Transplant changesets from src to dest"""
    url = TRANSPLANT_URL + '/transplant'
    headers = {'Content-Type': 'application/json'}
    data = {
        'src': src,
        'dst': dest,
        'items': [{'commit': changeset} for changeset in changesets]
    }
    try:
        r = requests.post(url, data=json.dumps(data), headers=headers)
    except requests.exceptions.ConnectionError:
        return
    return json.loads(r.text)
