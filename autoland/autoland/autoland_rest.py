#!/usr/bin/env python
import json
import logging
import os
import psycopg2
import urlparse

from flask import Flask, request, jsonify, Response, abort, make_response

from mozlog.structured import commandline

AUTH = None
DSN = None

app = Flask(__name__, static_url_path='', static_folder='')


@app.errorhandler(404)
def not_found(error):
    return make_response(jsonify({'error': 'Not found'}), 404)


def get_dbconn():
    global DSN

    if not DSN:
        with open(os.path.join(os.path.dirname(os.path.realpath(__file__)),
                               'config.json')) as f:
            DSN = json.load(f)['database']

    return psycopg2.connect(DSN)


def check_auth(user, passwd):
    global AUTH

    if not AUTH:
        with open(os.path.join(os.path.dirname(os.path.realpath(__file__)),
                               'config.json')) as f:
            AUTH = json.load(f)['auth']

    if user in AUTH and AUTH[user] == passwd:
        return True


@app.route('/autoland', methods=['POST'])
def autoland():
    """
    Autoland a patch from one tree to another.


    Example request json:

    {
      "tree": "mozilla-central",
      "revision": "9cc25f7ac50a",
      "destination": "try",
      "trysyntax": "try: -b o -p linux -u mochitest-1 -t none",
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
        insert into Transplant(tree,rev,destination,trysyntax,pingback_url)
        values (%s,%s,%s,%s,%s)
        returning id
    """

    cursor.execute(query, (request.json['tree'], request.json['rev'],
                           request.json['destination'],
                           request.json.get('trysyntax', ''),
                           request.json['pingback_url']))
    request_id = cursor.fetchone()[0]
    dbconn.commit()

    return jsonify({'request_id': request_id})


@app.route('/autoland/status/<request_id>')
def autoland_status(request_id):

    dbconn = get_dbconn()
    cursor = dbconn.cursor()

    query = """
        select tree,rev,destination,trysyntax,landed,result,pingback_url
        from Transplant
        where id = %(request_id)s
    """

    try:
        cursor.execute(query, ({'request_id': int(request_id)}))
    except ValueError:
        abort(404)

    row = cursor.fetchone()
    if row:
        result = {
            'tree': row[0],
            'rev': row[1],
            'destination': row[2],
            'trysyntax': row[3],
            'landed': row[4],
            'result': row[5],
            'pingback_url': row[6]
        }

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

    global DSN
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
