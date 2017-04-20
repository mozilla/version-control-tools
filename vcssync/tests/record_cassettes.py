#!/usr/bin/env python2.7
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

# This script is used to record betamax cassettes for use in tests.

from __future__ import absolute_import, unicode_literals

import argparse
import os

import betamax
import betamax_serializers.pretty_json as pretty_json
import github3


HERE = os.path.abspath(os.path.dirname(__file__))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('token', help='GitHub token')

    args = parser.parse_args()

    betamax.Betamax.register_serializer(pretty_json.PrettyJSONSerializer)

    with betamax.Betamax.configure() as config:
        config.cassette_library_dir = os.path.join(HERE, 'cassettes')

        # Replace real API token with a placeholder so it isn't leaked.
        config.define_cassette_placeholder(b'<AUTH_TOKEN>', args.token)

        # Force recording of all requests all the time.
        config.default_cassette_options['record_mode'] = 'all'

        # Make saved cassette files readable.
        config.default_cassette_options['serialize_with'] = 'prettyjson'

    client = github3.GitHub()

    # requests advertises gzip support by default (as it should!). However,
    # This means that HTTP response bodies are base64 encoded in the cassette
    # JSON, making them difficult to diff and audit for sensitive data. Since
    # the encoding of the HTTP response body isn't important for our testing,
    # disable it.
    client._session.headers.update({'Accept-Encoding': 'identity'})

    recorder = betamax.Betamax(client._session)

    with recorder.use_cassette('linearize-github-pull-request-messages'):
        # This test simply looks up a pull request and resolves more info about
        # the user who created it.
        client.login(token=args.token)
        client.pull_request('servo', 'servo', 16549)
        client.user('bholley')


if __name__ == '__main__':
    main()
