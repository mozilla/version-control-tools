import json
import requests

#TRANSPLANT_URL = 'http://transplant.infinity.com.ua'
TRANSPLANT_URL = 'http://localhost:5000'

def transplant(src, dest, changesets):
    url = TRANSPLANT_URL + '/transplant'
    headers = {'Content-Type': 'application/json'}
    data = {
        'src': src,
        'dst': dest,
        'commits': changesets
    }
    r = requests.post(url, data=json.dumps(data), headers=headers)
    return r.status_code, r.text
