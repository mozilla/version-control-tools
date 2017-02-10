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
                                  github_queue=c['pulse_github_queue'])

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
                              cwd='/', bufsize=0)
        message.ack()

    # Overlay Servo changesets from the pristine, converted repo onto
    # a Firefox repo in response to new hg changesets.
    def on_hgmo_message(body, message):
        if body['payload']['type'] != 'changegroup.1':
            message.ack()
            return

        repo_url = body['payload']['data']['repo_url']
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
                              cwd='/', bufsize=0)
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


def pulse_daemon():
    import argparse

    # Unbuffer stdout.
    sys.stdout = os.fdopen(sys.stdout.fileno(), 'w', 0)

    parser = argparse.ArgumentParser()
    parser.add_argument('config', help='Path to config file to load')

    args = parser.parse_args()

    config = load_config(args.config)

    root = logging.getLogger()
    handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter('%(name)s %(message)s')
    handler.setFormatter(formatter)
    root.addHandler(handler)

    run_pulse_listener(config)
