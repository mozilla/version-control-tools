import json
import requests


def post_job(host, tree, rev, destination, trysyntax, pingback_url, user, passwd):

    data = {
        'tree': tree,
        'rev': rev,
        'destination': destination,
        'trysyntax': trysyntax,
        'pingback_url': pingback_url
    }

    r = requests.post(host + '/autoland', data=json.dumps(data),
                      headers={'Content-Type': 'application/json'},
                      auth=(user, passwd))
    return r.status_code, r.text


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument('--host', required=True,
                        help='Host to which to post the job ' +
                             'e.g. http://localhost:8000')
    parser.add_argument('--tree', required=True,
                        help='Source tree of the revision')
    parser.add_argument('--rev', required=True, help='Revision to land')
    parser.add_argument('--destination', required=True,
                        help='Destination tree for the revision')
    parser.add_argument('--trysyntax', default='',
                        help='Try syntax to use if landing to try.')
    parser.add_argument('--pingback-url',
                        help='Endpoint to which to post results')
    parser.add_argument('--user', required=True, help='Autoland user')
    parser.add_argument('--passwd', required=True, help='Autoland password')
    args = parser.parse_args()

    print(post_job(args.host, args.tree, args.rev, args.destination,
                   args.trysyntax, args.pingback_url, args.user, args.passwd))
