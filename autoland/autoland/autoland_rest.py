#!/usr/bin/env python
import config
import json
import logging
import os
import psycopg2
import urlparse

from flask import Flask, request, jsonify, Response, abort, make_response

from mozlog.structured import commandline


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
      "tree": "mozilla-central",
      "rev": "9cc25f7ac50a",
      "destination": "try",
      "trysyntax": "try: -b o -p linux -u mochitest-1 -t none",
      "push_bookmark": "@",
      "pingback_url": "http://localhost/"
    }

    Both trysyntax and push_bookmark are optional.

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

    for field in ['tree', 'rev', 'destination', 'pingback_url']:
        if not field in request.json:
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


@app.route('/pullrequest/mozreview', methods=['POST'])
def pullrequest_mozreview():
    """
    Autoland a github pullrequest to a mozreview repo.

    Example request json for a github pull request:

    {
      "user": "cthulhu",
      "repo": "gecko-dev",
      "pullrequest": 1,
      "destination": "gecko",
      "bzuserid": 1,
      "bzcookie": "cookie",
      "bugid": 1,
      "pingback_url": "http://localhost/",
    }

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

    for field in ['user', 'repo', 'pullrequest', 'destination', 'bzuserid',
                  'bzcookie', 'bugid', 'pingback_url']:
        if not field in request.json:
            error = 'Bad request: missing json field: %s' % field
            return make_response(jsonify({'error': error}), 400)

    app.logger.info('received transplant request: %s' %
                    json.dumps(request.json))

    dbconn = get_dbconn()
    cursor = dbconn.cursor()

    query = """
        insert into MozreviewPullRequest(ghuser,repo,pullrequest,destination,
                                         bzuserid,bzcookie,bugid,pingback_url)
        values (%s,%s,%s,%s,%s,%s,%s,%s)
        returning id
    """
    cursor.execute(query, (request.json['user'], request.json['repo'],
                           request.json['pullrequest'],
                           request.json['destination'],
                           request.json['bzuserid'],
                           request.json['bzcookie'],
                           request.json['bugid'],
                           request.json['pingback_url']))

    request_id = cursor.fetchone()[0]
    dbconn.commit()

    return jsonify({'request_id': request_id})


@app.route('/pullrequest/mozreview/status/<request_id>')
def pullrequest_mozreview_status(request_id):

    dbconn = get_dbconn()
    cursor = dbconn.cursor()

    query = """
        select ghuser,repo,pullrequest,destination,bugid,landed,result
        from MozreviewPullRequest
        where id = %(request_id)s
    """

    try:
        cursor.execute(query, ({'request_id': int(request_id)}))
    except ValueError:
        abort(404)

    row = cursor.fetchone()
    if row:
        landed = row[5]

        result = {
            'user': row[0],
            'repo': row[1],
            'pullrequest': row[2],
            'destination': row[3],
            'bugid': row[4],
            'landed': landed,
            'result': '',
            'error_msg': ''
        }

        if landed:
            result['result'] = row[6]
        else:
            result['error_msg'] = row[6]

        return jsonify(result)

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
    commandline.add_logging_group(parser)
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO)

    app.logger.info('starting REST listener on port %d' % args.port)
    app.run(host="0.0.0.0", port=args.port, debug=False)


if __name__ == "__main__":
    main()
