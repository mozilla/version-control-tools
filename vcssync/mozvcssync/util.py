# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from __future__ import absolute_import, unicode_literals

import contextlib
import errno
import hashlib
import os
import pipes
import shutil

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
        run_hg(logger, repo, [b'--quiet', b'revert', b'--no-backup', b'--all'])
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


def hash_path(path):
    try:
        with open(path, 'rb') as fh:
            return hashlib.sha256(fh.read()).digest()
    except IOError as e:
        if e.errno != errno.ENOENT:
            raise

        return None


@contextlib.contextmanager
def monitor_hg_repo(repo_path, hg_paths=None):
    """Context manager to monitor a Mercurial repo for changes.

    Before the context manager is active, the Mercurial repo at
    ``repo_path`` is opened and state is collected.

    When the context manager closes, a similar sampling is performed.

    The context manager returns a dict describing the state of the repo. It
    has keys ``before`` and ``after`` which hold state from before and
    after the body of the context manager executes. It is currently up to the
    caller to perform diffing.

    Note: currently only the tip rev and node are recorded to compute for
    differences. This is insufficient to detect changes for all use cases. For
    example, it may not accurately detect certain strip operations.
    """
    hg_paths = hg_paths or []

    def get_state():
        with hglib.open(repo_path) as repo:
            tip = repo[b'tip']
            tip_rev = tip.rev()
            tip_node = tip.node()

        hashes = {path: hash_path(os.path.join(b'.hg', path))
                  for path in hg_paths}

        return {
            'tip_rev': tip_rev,
            'tip_node': tip_node,
            'hashes': hashes,
        }

    state = {'before': get_state()}

    try:
        yield state
    finally:
        state['after'] = get_state()


def apply_changes_from_list(logger, source_path, dest_path, files):
    """Updates `files` in `dest_path` from `source_path`.

    `files` should contain a list of all modified files, including files that
    have been deleted from `source_path`."""
    for filename in files:
        source_file = '%s/%s' % (source_path, filename)
        dest_file = '%s/%s' % (dest_path, filename)

        if os.path.exists(source_file):
            if os.path.exists(dest_file):
                logger.info('updating %s' % dest_file)
            else:
                logger.info('creating %s' % dest_file)

            path = os.path.dirname(dest_file)
            if not os.path.exists(path):
                os.mkdir(path)
            shutil.copy(source_file, dest_file)

        else:
            if os.path.exists(dest_file):
                logger.info('deleting %s' % dest_file)
                os.unlink(dest_file)

                # Delete empty directories.
                path = os.path.dirname(dest_file)
                try:
                    os.rmdir(path)
                    logger.info('deleting %s/' % path)
                except OSError as e:
                    if e.errno != errno.ENOTEMPTY:
                        raise
            else:
                logger.warn('%s already deleted' % dest_file)
