#!/usr/bin/env python
import argparse
import datetime
import httplib
import json
import logging
import os
import platform
import psycopg2
import re
import string

from flask import Flask, request, json, Response, abort

from mozlog.structured import (
    commandline,
    formatters,
    handlers,
    structuredlog,
)

DSN = None

app = Flask(__name__, static_url_path='', static_folder='')

def get_dbconn():
    global DSN

    if not DSN:
        with open('database-config.json') as f:
            DSN = json.load(f)['dsn']

    return psycopg2.connect(DSN)


@app.route('/autoland', methods=['POST'])
def autoland():
    """
    Autoland a patch from one tree to another.


    Example request json:

    {
      'tree': 'mozilla-central',
      'revision': '9cc25f7ac50a',
      'destination': 'try',
      'trysyntax': 'try: -b o -p linux -u mochitest-1 -t none',
    }

    Returns an id which can be used to get the status of the autoland
    request.

    """

    app.logger.info('received transplant request: %s' % json.dumps(request.json)) 

    dbconn = get_dbconn()
    cursor = dbconn.cursor()

    query = """
        insert into Transplant(tree,rev,destination,trysyntax)
        values (%s,%s,%s,%s)
        returning id
    """

    cursor.execute(query, (request.json['tree'], request.json['rev'],
                           request.json['destination'],
                           request.json['trysyntax']))
    request_id = cursor.fetchone()[0]
    dbconn.commit()

    result = json.dumps({'request_id': request_id})

    headers = [
        ("Content-Type", "application/json"),
        ("Content-Length", str(len(result)))
    ]
    return Response(result, status=200, headers=headers)


@app.route('/autoland/status/<request_id>')
def autoland_status(request_id):

    dbconn = get_dbconn()
    cursor = dbconn.cursor()

    query = """
        select tree,rev,destination,trysyntax,landed,result from Transplant
        where id = %s
    """
    cursor.execute(query, (request_id))

    row = cursor.fetchone()
    if row:
        result = json.dumps({'tree': row[0],
                             'rev': row[1],
                             'destination': row[2],
                             'trysyntax': row[3],
                             'landed': row[4],
                             'result': row[5]})

        headers = [
            ("Content-Type", "application/json"),
            ("Content-Length", str(len(result)))
        ]

        return Response(result, status=200, headers=headers)

    return Response('', status=404)

@app.route('/')
def hi_there():
    result = 'Welcome to Autoland'

    headers = [
        ("Content-Type", "text/plain"),
        ("Content-Length", str(len(result)))
    ]

    return Response(result, status=200, headers=headers)


def main():
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
