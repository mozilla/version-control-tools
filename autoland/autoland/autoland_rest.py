#!/usr/bin/env python
import base64
import hmac
import json
import logging
import urlparse

import ipaddress
import psycopg2
from flask import Flask, request, jsonify, Response, abort, make_response

import config

app = Flask(__name__, static_url_path='', static_folder='')


@app.errorhandler(404)
def not_found(error):
    return make_response(jsonify({'error': 'Not found'}), 404)


@app.errorhandler(500)
def internal_server_error(error):
    return make_response(jsonify({'error': str(error)}), 500)


def get_dbconn():
    return psycopg2.connect(config.get('database'))


def compare_digest_backport(a, b):
    # hmac.compare_digest requires Python 2.7.7, while autoland has 2.7.6.
    # This implementation is from urllib3.
    result = abs(len(a) - len(b))
    for l, r in zip(bytearray(a), bytearray(b)):
        result |= l ^ r
    return result == 0

compare_digest = getattr(hmac, 'compare_digest', compare_digest_backport)


def check_auth(user, passwd):
    auth = config.get('auth')
    return compare_digest(auth.get(user, '').encode('utf8'),
                          passwd.encode('utf8'))


def check_pingback_url(pingback_url):
    try:
        url = urlparse.urlparse(pingback_url)
    except ValueError:
        return False

    if url.scheme not in ('http', 'https'):
        return False

    # Allow pingbacks to loopback and private IPs (for dev/test).
    if url.hostname == 'localhost':
        return True
    try:
        ip = ipaddress.ip_address(url.hostname)
        if ip.is_loopback or ip.is_private:
            return True
    except ValueError:
        # Ignore hostnames and invalid addresses.
        pass

    # Allow pingbacks to whitelisted hosts from config.json
    return url.hostname in config.get('pingback', {})


def check_patch_url(patch_url):
    try:
        url = urlparse.urlparse(patch_url)
    except ValueError:
        logging.error('invalid patch_url "%s": malformed url' % patch_url)
        return False

    # http is only supported when using loopback and private IPs (for dev/test)
    if url.scheme in ('http', 'https'):
        if url.hostname == 'localhost':
            return True
        try:
            ip = ipaddress.ip_address(url.hostname)
            if ip.is_loopback or ip.is_private:
                return True
        except ValueError:
            # Ignore hostnames and invalid addresses.
            pass
        logging.error('invalid patch_url "%s": public http url' % patch_url)

    # Deployed environments must use the s3 scheme.  s3://bucket/path/to/file
    if url.scheme != 's3':
        logging.error('invalid patch_url "%s": not a s3:// url' % patch_url)
        return False

    # Allow patches only from buckets configured in config.json.
    if url.hostname not in config.get('patch_url_buckets', {}):
        logging.error('invalid patch_url "%s": not whitelisted by config'
                      % patch_url)
        return False

    return True


def validate_request(request):
    if request.json is None:
        raise ValueError('missing json')
    request_json = request.json

    required = {'ldap_username', 'tree', 'rev', 'pingback_url', 'destination'}
    optional = set()

    is_try = 'trysyntax' in request_json
    is_patch = 'patch_urls' in request_json
    if config.testing() and not is_patch:
        is_patch = 'patch' in request_json

    if (not is_patch) and not ('trysyntax' in request_json or
                               'commit_descriptions' in request_json):
        raise ValueError('one of trysyntax or commit_descriptions must be '
                         'specified')

    if not is_try and not is_patch:
        # Repo transplant.
        required.add('commit_descriptions')
        optional.add('push_bookmark')

    elif not is_try and is_patch:
        # Patch transplant.
        if config.testing():
            optional.add('patch_urls')
            optional.add('patch')
        else:
            required.add('patch_urls')
        optional.add('push_bookmark')

    elif is_try and not is_patch:
        # Repo try.
        required.add('trysyntax')

    elif is_try and is_patch:
        # Patch try.
        raise ValueError('trysyntax is not supported with patch_urls')

    request_fields = set(request_json.keys())

    missing = required - request_fields
    if missing:
        raise ValueError('missing required field%s: %s' % (
            '' if len(missing) == 1 else 's',
            ', '.join(sorted(missing))))

    extra = request_fields - (required | optional)
    if extra:
        raise ValueError('unexpected field%s: %s' % (
            '' if len(extra) == 1 else 's',
            ', '.join(sorted(extra))))

    if not check_pingback_url(request_json['pingback_url']):
        raise ValueError('bad pingback_url')

    if is_patch:
        if config.testing() and ('patch_urls' in request_json
                                 and 'patch' in request_json):
            raise ValueError('cannot specify both patch_urls and patch')

        if 'patch_urls' in request_json:
            for patch_url in request_json['patch_urls']:
                if not check_patch_url(patch_url):
                    raise ValueError('bad patch_url')

        if 'patch' in request_json:
            try:
                base64.b64decode(request_json['patch'])
            except TypeError:
                raise ValueError('malformed base64 in patch')


@app.route('/autoland', methods=['POST'])
def autoland():
    """
    Autoland a patch from one tree to another.

    Example repository based landing request:
    (All fields are required except for push_bookmark)

    {
      "ldap_username": "cthulhu@mozilla.org",
      "tree": "mozilla-central",
      "rev": "9cc25f7ac50a",
      "destination": "gecko",
      "commit_descriptions": {"9cc25f7ac50a": "bug 1 - did stuff r=gps"},
      "pingback_url": "http://localhost/",
      "push_bookmark": "@"
    }

    Example repository based try request:
    (All fields are required)

    {
      "ldap_username": "cthulhu@mozilla.org",
      "tree": "mozilla-central",
      "rev": "9cc25f7ac50a",
      "destination": "try",
      "pingback_url": "http://localhost/",
      "trysyntax": "try: -b o -p linux -u mochitest-1 -t none"
    }

    Example patch based landing request:

    {
      "ldap_username": "cthulhu@mozilla.org",
      "tree": "mozilla-central",
      "rev": "1235",
      "patch_urls": ["s3://bucket/123456789.patch"],
      "destination": "gecko",
      "pingback_url": "http://localhost/",
      "push_bookmark": "@"
    }

    When "testing" is set to `true` in config.json, patches can be provided
    inline, base64 encoded:

    {
      "ldap_username": "cthulhu@mozilla.org",
      "tree": "mozilla-central",
      "rev": "1235",
      "patch": "dGhpcyBpcyBub3QgYSByZWFsIHBhdGNoCg==",
      "destination": "gecko",
      "pingback_url": "http://localhost/",
      "push_bookmark": "@"
    }

    Patch based try requests are not supported.

    Differences between repository and patch based requests:
      "rev" changes from sha of source tree to unique ID
      "patch_urls" added with URLs to the patch files
      "commit_descriptions" removed

    Returns an id which can be used to get the status of the autoland
    request.

    """

    auth = request.authorization
    auth_response = {'WWW-Authenticate': 'Basic realm="Login Required"'}
    if not auth:
        return Response('Login required', 401, auth_response)
    if not check_auth(auth.username, auth.password):
        logging.warn('Failed authentication for "%s" from %s' % (
            auth.username, request.remote_addr))
        return Response('Login required', 401, auth_response)

    try:
        validate_request(request)
    except ValueError as e:
        app.logger.warn('Bad Request from %s: %s' % (request.remote_addr, e))
        return make_response(jsonify({'error': 'Bad request: %s' % e}), 400)

    dbconn = get_dbconn()
    cursor = dbconn.cursor()

    query = """
        SELECT created, request->>'ldap_username'
          FROM Transplant
         WHERE landed IS NULL
               AND request->>'rev' = %s
               AND request->>'destination' = %s
    """
    cursor.execute(query, (request.json['rev'], request.json['destination']))
    in_flight = cursor.fetchone()
    if in_flight:
        error = ('Bad Request: a request to land revision %s to %s is already '
                 'in progress'
                 % (request.json['rev'], request.json['destination']))
        app.logger.warn(
            '%s from %s at %s' % (error, in_flight[0], in_flight[1]))
        return make_response(jsonify({'error': error}), 400)

    app.logger.info('received transplant request: %s' %
                    json.dumps(request.json))

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
