import json
import requests

#TRANSPLANT_URL = 'http://transplant.infinity.com.ua'
TRANSPLANT_URL = 'http://localhost:5000'

def transplant(src, dest, changesets, message):
    """Transplant changsets from src to dest using the provided message"""
    url = TRANSPLANT_URL + '/transplant'
    headers = {'Content-Type': 'application/json'}
    data = {
        'src': src,
        'dst': dest,
        'items': [
            {'revset': ' + '.join(changesets),
             'message': message}
        ]
    }
    try:
        r = requests.post(url, data=json.dumps(data), headers=headers)
    except requests.exceptions.ConnectionError:
        return
    return json.loads(r.text)
