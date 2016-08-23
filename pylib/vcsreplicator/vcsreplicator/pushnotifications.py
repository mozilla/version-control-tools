# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from __future__ import absolute_import, unicode_literals

import logging
import os

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

    if name == 'heartbeat-1':
        logger.warn('%s message not relevant; ignoring' % name)
        consumer.commit(partitions=[partition])
        return

    # All other messages should be associated with a repo and have a "path"
    # key.
    path = payload['path']
    public_url = config.get_public_url_from_wire_path(path)

    if not public_url:
        logger.warn('no public URL could be resolved for %s; not sending notification' % path)
        consumer.commit(partitions=[partition])
        return

    if config.c.has_section('ignore_paths'):
        for prefix, _ in config.c.items('ignore_paths'):
            if path.startswith(prefix):
                logger.warn('ignoring repo because path in ignore list: %s' % path)
                consumer.commit(partitions=[partition])
                return

    local_path = config.parse_wire_repo_path(path)

    # FUTURE if we ever write a "repo deleted" message, this should be updated to
    # send the message through.
    if not os.path.exists(local_path):
        logger.warn('repository %s does not exist; ignoring notification' % local_path)
        consumer.commit(partitions=[partition])
        return

    cbargs = dict(cbkwargs or {})
    firecb = True

    if name in ('hg-changegroup-1', 'hg-changegroup-2'):
        message_type = 'changegroup.1'
        cbargs['data'] = _get_changegroup_payload(local_path,
                                                  public_url,
                                                  payload['heads'],
                                                  payload['source'])
    elif name in ('hg-repo-init-1', 'hg-repo-init-2'):
        message_type = 'newrepo.1'
        cbargs['data'] = {
            'repo_url': public_url,
        }
    elif name == 'hg-pushkey-1':
        res = _get_pushkey_payload(local_path, public_url,
                                   payload['namespace'],
                                   payload['key'],
                                   payload['old'],
                                   payload['new'],
                                   payload['ret'])
        if res:
            message_type, cbargs['data'] = res
        else:
            firecb = False

    else:
        # Ack unsupported messages.
        logger.warn('%s message not relevant to push notifier; ignoring' % name)
        firecb = False

    if firecb:
        cb(message_type=message_type, **cbargs)

    consumer.commit(partitions=[partition])


def _get_changegroup_payload(local_path, public_url, heads, source):
    logger.warn('querying pushlog data for %s' % local_path)

    # Resolve the push IDs for these changesets.
    with hglib.open(local_path, encoding='utf-8') as hgclient:
        # We cheat and only request pushlog entries for heads. There may be
        # some scenarios where we want pushlog entries for all nodes. But as
        # of hg-changegroup-2 messages we don't record every node in the
        # changegroup (just the count), so the full set of nodes isn't
        # available. We shouldn't be seeing too many changegroup messages
        # where a message doesn't correspond to a single push, so this shortcut
        # should be acceptable.
        revs = [n.encode('latin1') for n in heads]
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

        return {
            'repo_url': public_url,
            'heads': heads,
            'source': source,
            'pushlog_pushes': [v for k, v in sorted(pushes.items())],
        }


def _get_pushkey_payload(local_path, public_url, namespace, key, old, new, ret):
    """Turn a pushkey replication message into an event message.

    Returns a 2-tuple of (message_type, data) on success or None if no message
    is to be generated.
    """
    return None
