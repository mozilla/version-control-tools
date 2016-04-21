# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from __future__ import absolute_import, unicode_literals

import logging

import hglib


logger = logging.getLogger('vcsreplicator.pushnotifications')


def consume_one(config, consumer, cb, timeout=0.1, alive=None, cbkwargs=None):
    """Consume at most a single message and notify the callback if necessary.

    The callback will receive arguments describing the push along with any
    other arguments from ``cbkwargs`` that are specified.
    """
    r = consumer.get_message(timeout=timeout)
    if not r:
        return

    partition, message, payload = r
    name = payload['name']

    # We're only interested in changegroup messages because they correspond
    # to pushes. Ack all messages that aren't relevant.
    if name != 'hg-changegroup-1':
        logger.warn('%s message not relevant to push notifier; ignoring' % name)
        consumer.commit(partitions=[partition])
        return

    path = payload['path']
    public_url = config.get_public_url_from_wire_path(path)

    if not public_url:
        logger.warn('no public URL could be resolved for %s; not sending notification' % path)
        return

    if config.c.has_section('ignore_paths'):
        for prefix, _ in config.c.items('ignore_paths'):
            if path.startswith(prefix):
                logger.warn('ignoring repo because path in ignore list: %s' % path)
                return

    local_path = config.parse_wire_repo_path(path)

    logger.warn('querying pushlog data for %s' % local_path)

    # Resolve the push IDs for these changesets.
    with hglib.open(local_path, encoding='utf-8') as hgclient:
        revs = [n.encode('latin1') for n in payload['nodes']]
        template = b'{node}\\0{pushid}\\0{pushuser}\\0{pushdate}\n'
        args = hglib.util.cmdbuilder(b'log', b'--hidden', r=revs, template=template)
        out = hgclient.rawcommand(args)

        pushes = {}

        for line in out.splitlines():
            line = line.strip()
            if not line:
                continue

            node, pushid, pushuser, pushtime = line.split('\0')
            # Not all changegroup events have corresponding pushlog entries.
            # This should be rare.
            if not pushid:
                logger.warn('pushlog data missing!')
                continue

            pushid = int(pushid)
            pushtime = int(pushtime)

            q = 'startID=%d&endID=%d' % (pushid - 1, pushid)

            pushes.setdefault(pushid, {
                'pushid': pushid,
                'user': pushuser,
                'time': pushtime,
                'push_json_url': '%s/json-pushes?version=2&%s' % (public_url, q),
                'push_full_json_url': '%s/json-pushes?version=2&full=1&%s' % (public_url, q)
            })

    cbargs = {
        'repo_url': public_url,
        'heads': payload['heads'],
        'source': payload['source'],
        'pushlog_pushes': [v for k, v in sorted(pushes.items())],
    }

    if cbkwargs:
        cbargs.update(cbkwargs)

    cb(**cbargs)
    consumer.commit(partitions=[partition])
