# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from __future__ import absolute_import, unicode_literals

import os
import pipes

import github3
import hglib


def run_hg(logger, client, args):
    """Run a Mercurial command through hgclient and log output."""
    logger.warn('executing: hg %s' % ' '.join(map(pipes.quote, args)))
    out = hglib.util.BytesIO()

    def write(data):
        logger.warn(b'hg> %s' % data.rstrip())
        out.write(data)

    out_channels = {b'o': write, b'e': write}
    ret = client.runcommand(args, {}, out_channels)

    if ret:
        raise hglib.error.CommandError(args, ret, out.getvalue(), b'')

    return out.getvalue()


def clean_hg_repo(logger, path):
    """Clean a Mercurial working directory."""
    logger.warn('reverting all local changes and purging %s' % path)
    with hglib.open(path, 'utf-8', [b'extensions.purge=']) as repo:
        run_hg(logger, repo, [b'revert', b'--no-backup', b'--all'])
        run_hg(logger, repo, [b'purge', b'--all'])


def get_github_client(token):
    """Obtain a github3 client using an API token for authentication.

    If the ``BETAMAX_LIBRARY_DIR`` and ``BETAMAX_CASSETTE`` environment
    variables are defined, the ``requests.Session`` used by the client
    will be hooked up to betamax and pre-recorded HTTP requests will be used
    instead of incurring actual requests. When betamax is active, the auth
    token is not relevant.
    """

    gh = github3.GitHub()

    betamax_library_dir = os.environ.get('BETAMAX_LIBRARY_DIR')
    betamax_cassette = os.environ.get('BETAMAX_CASSETTE')

    if betamax_library_dir and betamax_cassette:
        # Delay import because only needed for testing.
        import betamax

        with betamax.Betamax.configure() as config:
            config.cassette_library_dir = betamax_library_dir

            # We don't want requests hitting the network at all.
            config.default_cassette_options['record_mode'] = 'none'

        recorder = betamax.Betamax(gh._session)
        recorder.use_cassette(betamax_cassette)
        recorder.start()

    gh.login(token=token)

    return gh
