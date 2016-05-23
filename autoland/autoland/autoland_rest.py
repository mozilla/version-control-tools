#!/usr/bin/env python
import config
import json
import logging
import psycopg2
import urlparse

from flask import Flask, request, jsonify, Response, abort, make_response


app = Flask(__name__, static_url_path='', static_folder='')


@app.errorhandler(404)
def not_found(error):
    return make_response(jsonify({'error': 'Not found'}), 404)


@app.errorhandler(500)
def internal_server_error(error):
    return make_response(jsonify({'error': str(error)}), 500)


def get_dbconn():
    return psycopg2.connect(config.get('database'))


def check_auth(user, passwd):
    auth = config.get('auth')
    if user in auth and auth[user] == passwd:
        return True


@app.route('/autoland', methods=['POST'])
def autoland():
    """
    Autoland a patch from one tree to another.

    Example request json:

    {
      "ldap_username": "cthulhu@mozilla.org",
      "tree": "mozilla-central",
      "rev": "9cc25f7ac50a",
      "destination": "try",
      "trysyntax": "try: -b o -p linux -u mochitest-1 -t none",
      "push_bookmark": "@",
      "commit_descriptions": {"9cc25f7ac50a": "bug 1 - did stuff r=gps"},
      "pingback_url": "http://localhost/"
    }

    The trysyntax, push_bookmark and commit_descriptions fields are
    optional, but one of trysyntax or commit_descriptions must be specified.

    Returns an id which can be used to get the status of the autoland
    request.

    """

    auth = request.authorization
    if not auth or not check_auth(auth.username, auth.password):
        return Response('Login required', 401,
                        {'WWW-Authenticate': 'Basic realm="Login Required"'})

    if request.json is None:
        error = 'Bad request: missing json'
        return make_response(jsonify({'error': error}), 400)

    for field in ['ldap_username', 'tree', 'rev', 'destination',
                  'pingback_url']:
        if field not in request.json:
            error = 'Bad request: missing json field: %s' % field
            return make_response(jsonify({'error': error}), 400)

    try:
        parsed = urlparse.urlparse(request.json['pingback_url'])
        if 'http' not in parsed.scheme:
            error = 'Bad request: bad pingback_url'
            return make_response(jsonify({'error': error}), 400)
    except:
        error = 'Bad request: bad pingback_url'
        return make_response(jsonify({'error': error}), 400)

    if not request.json.get('ldap_username'):
        error = 'Bad request: ldap_username must be specified'
        return make_response(jsonify({'error': error}), 400)

    if not (request.json.get('trysyntax') or
            request.json.get('commit_descriptions')):
        error = ('Bad request: one of trysyntax or commit_descriptions must '
                 'be specified.')
        return make_response(jsonify({'error': error}), 400)

    app.logger.info('received transplant request: %s' %
                    json.dumps(request.json))

    dbconn = get_dbconn()
    cursor = dbconn.cursor()

    query = """
        insert into Transplant(destination, request)
        values (%s, %s)
        returning id
    """

    cursor.execute(query, (request.json['destination'],
                           json.dumps(request.json)))

    request_id = cursor.fetchone()[0]
    dbconn.commit()

    return jsonify({'request_id': request_id})


@app.route('/autoland/status/<request_id>')
def autoland_status(request_id):

    dbconn = get_dbconn()
    cursor = dbconn.cursor()

    query = """
        select destination, request, landed, result
        from Transplant
        where id = %(request_id)s
    """

    try:
        cursor.execute(query, ({'request_id': int(request_id)}))
    except ValueError:
        abort(404)

    row = cursor.fetchone()
    if row:
        destination, request, landed, result = row

        status = request.copy()
        del status['pingback_url']
        status['destination'] = destination
        status['landed'] = landed
        status['result'] = result if landed else ''
        status['error_msg'] = result if not landed else ''

        return jsonify(status)

    abort(404)


@app.route('/')
def hi_there():
    result = 'Welcome to Autoland'

    headers = [
        ("Content-Type", "text/plain"),
        ("Content-Length", str(len(result)))
    ]

    return Response(result, status=200, headers=headers)


def main():
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument('--port', type=int, default=8000,
                        help='Port on which to listen')
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO)

    app.logger.info('starting REST listener on port %d' % args.port)
    app.run(host="0.0.0.0", port=args.port, debug=False)


if __name__ == "__main__":
    main()
