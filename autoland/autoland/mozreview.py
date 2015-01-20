import json
import requests

MOZREVIEW_URL = 'https://reviewboard-dev.allizom.org/api'
#MOZREVIEW_URL = 'http://localhost:55563/api'


def read_credentials():
    user, passwd = open('credentials/mozreview.txt').read().strip().split(',')
    return (user, passwd)


def update_review(auth, review_request_id, rev):
    data = {'extra_data.p2rb.autoland_try': json.dumps({'status': 'started',
                                                        'commitId': rev}),
            'public': 'true'}
    try:
        r = requests.post(MOZREVIEW_URL + '/review-requests/' + str(review_request_id) + '/draft/',
                         auth=auth,
                         data=data)
        # TODO: log this
        print(r.status_code, r.text)
    except requests.exceptions.ConnectionError:
        return
    return r.status_code == 201


def publish_review(auth, review_request_id):
    data = {'public': 'true'}
    try:
        r = requests.post(MOZREVIEW_URL + '/review-requests/' + str(review_request_id) + '/draft/',
                         auth=auth,
                         data=data)
        # TODO: log this
        print(r.status_code, r.text)
    except requests.exceptions.ConnectionError:
        return
    return r.status_code == 201


if __name__ == '__main__':
    auth = read_credentials()
    print(update_review(auth, 364, '6630019d3913'))
    print(publish_review(auth, 364))
