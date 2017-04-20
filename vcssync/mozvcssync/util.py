# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from __future__ import absolute_import, unicode_literals

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


def get_github_client(token):
    """Obtain a github3 client using an API token for authentication."""

    gh = github3.GitHub()
    gh.login(token=token)

    return gh
