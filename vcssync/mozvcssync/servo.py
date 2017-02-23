# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from __future__ import absolute_import, print_function, unicode_literals

"""Functionality to support VCS syncing for Servo."""

import logging
import os
import subprocess
import sys

from ConfigParser import (
    RawConfigParser,
)

from . import (
    pulse,
)


logger = logging.getLogger('mozvcssync.servo')


def run_pulse_listener(c):
    """Trigger events from Pulse messages."""
    consumer = pulse.get_consumer(userid=c['pulse_userid'],
                                  password=c['pulse_password'],
                                  hostname=c['pulse_host'],
                                  port=c['pulse_port'],
                                  ssl=c['pulse_ssl'],
                                  github_exchange=c['pulse_github_exchange'],
                                  github_queue=c['pulse_github_queue'],
                                  hgmo_exchange=c['pulse_hgmo_exchange'],
                                  hgmo_queue=c['pulse_hgmo_queue'])

    # Trigger linearization + hg conversion after git push.
    def on_github_message(body, message):
        # We only care about push events.
        if body['event'] != 'push':
            logger.warn('ignoring non-push event: %s' % body['event'])
            message.ack()
            return

        # We only care about activity to the configured repository.
        repo_name = body['payload']['repository']['full_name']
        if repo_name != c['servo_github_name']:
            logger.warn('ignoring push for non-monitored repo: %s' % repo_name)
            message.ack()
            return

        ref = body['payload']['ref']
        logger.warn('observed push to %s of %s' % (ref, repo_name))

        if ref != c['servo_fetch_ref']:
            message.ack()
            return

        # Trigger the systemd unit that will linearize the Git repo
        # and convert to Mercurial. It does all the heavy lifting.
        #
        # `systemctl start` will block. This is fine. We want to wait
        # for the conversion to finish in case there are multiple remote
        # pushes queued up. Otherwise, there is a race condition between
        # the initial run finishing and subsequent Pulse events arriving.
        # If a subsequent notification is handled when the service is
        # running, it will no-op and we may not see its push.
        logger.warn('triggering linearization and conversion...')
        subprocess.check_call([b'/bin/sudo',
                               b'/usr/bin/systemctl', b'start',
                               b'servo-linearize.service'],
                              cwd='/', bufsize=1)
        message.ack()

    # Overlay Servo changesets from the pristine, converted repo onto
    # a Firefox repo in response to new hg changesets.
    def on_hgmo_message(body, message):
        if body['payload']['type'] != 'changegroup.1':
            message.ack()
            return

        repo_url = body['payload']['data']['repo_url']
        logger.warn('observed push to %s' % repo_url)
        if repo_url != c['hg_converted']:
            message.ack()
            return

        heads = body['payload']['data']['heads']
        if len(heads) != 1:
            raise Exception('unexpected heads count in upstream')

        revision = heads[0].encode('ascii')
        logger.warn('overlaying servo-linear changeset %s' % revision)
        subprocess.check_call([b'/bin/sudo',
                               b'/usr/bin/systemctl', b'start',
                               b'servo-overlay.service'],
                              cwd='/', bufsize=1)
        message.ack()

    consumer.github_callbacks.append(on_github_message)
    consumer.hgmo_callbacks.append(on_hgmo_message)

    try:
        with consumer:
            consumer.listen_forever()
    except KeyboardInterrupt:
        pass


def load_config(path):
    c = RawConfigParser()
    c.read(path)

    d = {}
    d.update(c.items('servo'))

    d['pulse_port'] = c.getint('servo', 'pulse_port')
    d['pulse_ssl'] = c.getboolean('servo', 'pulse_ssl')

    return d


def configure_stdout():
    # Unbuffer stdout.
    sys.stdout = os.fdopen(sys.stdout.fileno(), 'w', 1)

    # Log to stdout.
    root = logging.getLogger()
    handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter('%(name)s %(message)s')
    handler.setFormatter(formatter)
    root.addHandler(handler)


def pulse_daemon():
    import argparse

    configure_stdout()

    parser = argparse.ArgumentParser()
    parser.add_argument('config', help='Path to config file to load')

    args = parser.parse_args()

    config = load_config(args.config)
    run_pulse_listener(config)


def tree_is_open(tree):
    """Return if the specified tree is open according to treestatus.m.o"""
    import requests

    # Allow tests to set tree status directly.
    if 'TEST_TREESTATUS' in os.environ:
        if os.getenv('TEST_TREESTATUS') == 'error':
            raise Exception('Failed to determine tree status')
        return os.getenv('TEST_TREESTATUS') == 'open'

    r = None
    try:
        r = requests.get('https://treestatus.mozilla-releng.net/trees/' + tree)
        if r.status_code == 200:
            return r.json()['result']['status'] == 'open'
        elif r.status_code == 404:
            raise Exception('Unrecognised tree "%s"' % tree)
        else:
            raise Exception(
                'Unexpected response from treestatus API for tree "%s": %s'
                % (tree, r.status_code))
    except KeyError:
        if r is not None:
            logger.error('Malformed treestatus response: %s' % r.json())
        raise Exception(
            'Malformed response from treestatus API for tree "%s"' % tree)
    except Exception as e:
        raise Exception(
            'Failed to determine treestatus for %s: %s' % (tree, str(e)))


def overlay_cli():
    """Wrapper around overlay-hg-repos to perform servo specific tasks."""
    import argparse

    configure_stdout()

    parser = argparse.ArgumentParser()
    # Arguments that are passed to mozvcssync.cli:overlay_hg_repos_cli.
    parser.add_argument('--hg', help='hg executable to use'),
    parser.add_argument('--into', required=True,
                        help='Subdirectory into which changesets will be '
                             'applied')
    parser.add_argument('source_repo_url',
                        help='URL of repository whose changesets will be '
                             'overlayed')
    parser.add_argument('dest_repo_url',
                        help='URL of repository where changesets will be '
                             'overlayed')
    parser.add_argument('dest_repo_path',
                        help='Local path to clone of <dest_repo_url>')
    parser.add_argument('--result-push-url',
                        help='URL where to push the overlayed result')
    # Arguments for this script.
    parser.add_argument('--overlay-hg-repos', default='overlay-hg-repos',
                        help='Path overlay_hg_repos')
    parser.add_argument('--push-tree',
                        help='Name of tree to check on treestatus.mozilla.org '
                             'before pushing')

    args = parser.parse_args()

    # Ensure the tree is open before starting.
    try:
        if args.result_push_url and args.push_tree:
            push_tree = args.push_tree
            if not tree_is_open(push_tree):
                logger.warn('tree "%s" is closed, unable to continue'
                            % push_tree)
                sys.exit(0)
    except Exception as e:
        logger.error('abort: %s' % str(e))
        sys.exit(1)

    # Tree is open, overlay.
    overlay_hg_repos = [
        args.overlay_hg_repos,
        args.source_repo_url,
        args.dest_repo_url,
        args.dest_repo_path,
        '--into', args.into,
    ]
    if args.result_push_url:
        overlay_hg_repos.extend(['--result-push-url', args.result_push_url])
    if args.hg:
        overlay_hg_repos.extend(['--hg', args.hg])

    try:
        subprocess.check_call(overlay_hg_repos)
    except Exception as e:
        # A stack track from here is not useful.
        logger.error('abort: %s' % str(e))
        sys.exit(1)
