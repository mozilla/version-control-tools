# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from __future__ import absolute_import, unicode_literals

import json
import logging
import os
import sys

import hglib

from .config import (
    Config,
)
from .consumer import (
    Consumer,
)
from .daemon import (
    run_in_loop,
)

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
        cb(message_type=message_type, partition=partition, message=message,
           created=payload['_original_created'], **cbargs)

    consumer.commit(partitions=[partition])


def _get_pushlog_info(hgclient, public_url, revs):
    template = b'{node}\\0{pushid}\\0{pushuser}\\0{pushdate}\n'
    args = hglib.util.cmdbuilder(b'log', hidden=True, r=revs, template=template)
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
            'push_full_json_url': '%s/json-pushes?version=2&full=1&%s' % (public_url, q),
        })

    return pushes


def _get_changegroup_payload(local_path, public_url, heads, source):
    # Resolve the push IDs for these changesets.
    # We cheat and only request pushlog entries for heads. There may be
    # some scenarios where we want pushlog entries for all nodes. But as
    # of hg-changegroup-2 messages we don't record every node in the
    # changegroup (just the count), so the full set of nodes isn't
    # available. We shouldn't be seeing too many changegroup messages
    # where a message doesn't correspond to a single push, so this shortcut
    # should be acceptable.
    revs = [n.encode('latin1') for n in heads]
    logger.warn('querying pushlog data for %s' % local_path)
    with hglib.open(local_path, encoding='utf-8') as hgclient:
        pushes = _get_pushlog_info(hgclient, public_url, revs)

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
    if namespace == 'obsolete':
        return _get_obsolete_pushkey_message(local_path, public_url, new)

    logger.warn('%s pushkey namespace not handled; ignoring' % namespace)
    return None


def _get_obsolete_pushkey_message(local_path, public_url, rawdata):
    logger.warn('processing obsolete pushkey message for %s' % public_url)

    # ASSERTION: vcsreplicator extension loaded in system/user config.
    with hglib.open(local_path, encoding='utf-8') as hgclient:
        out = hgclient.rawcommand([b'debugbase85obsmarkers', rawdata])
        markers = json.loads(out)
        logger.warn('processing %d obsolete markers' % len(markers))

        def rev_info(node):
            template = b'{node}\\0{desc}\\0{pushid}'
            args = hglib.util.cmdbuilder(b'log', hidden=True, r=node,
                                         template=template)
            # Mercurial will abort with "unknown revision" if you give it
            # 40 character hash that isn't known.
            try:
                out = hgclient.rawcommand(args)
                return out.split(b'\0')
            except hglib.error.CommandError as e:
                if b'unknown revision' in e.err:
                    return None
                else:
                    raise

        def node_payload(node):
            assert len(node) == 40
            if isinstance(node, unicode):
                node = node.encode('latin1')

            rev = rev_info(node)

            # Determine if changeset is visible/hidden..
            if rev:
                args = hglib.util.cmdbuilder(b'log', r=node, template=b'{node}')
                try:
                    out = hgclient.rawcommand(args)
                    visible = bool(out.strip())
                except hglib.error.CommandError as e:
                    if b'hidden revision' in e.err:
                        visible = False
                    else:
                        visible = None
            else:
                visible = None

            # Obtain pushlog entry for this node.
            if rev and rev[2]:
                pushes = _get_pushlog_info(hgclient, public_url, [node])
                if pushes:
                    push = pushes[int(rev[2])]
                else:
                    push = None
            else:
                push = None

            return {
                'node': node,
                'known': bool(rev),
                'visible': visible,
                'desc': rev[1] if rev else None,
                'push': push,
            }

        data = []

        for marker in markers:
            # We collect data about the new and old changesets (if available)
            # because the repo may not expose information on hidden
            # changesets to public consumers.
            precursor = node_payload(marker['precursor'])
            successors = [node_payload(node) for node in marker['successors']]

            user = None
            for m in marker['metadata']:
                if m[0] == u'user':
                    user = m[1].encode('utf-8')

            data.append({
                'precursor': precursor,
                'successors': successors,
                'user': user,
                'time': marker['date'][0],
            })

    return 'obsolete.1', {
        'repo_url': public_url,
        'markers': data,
    }


def run_cli(config_section, cb, validate_config=None):
    """Runs a CLI notifier program.

    All the CLI notifier programs have the same interface. They accept a
    path to a config file. A function argument says which section in that
    config file to load.

    A ``cb`` function is called with the config, message_type, and message
    data for each replication related message seen. This data has been
    processed by ``consume_one``, so extra metdata from the VCS repository is
    available.

    If ``validate_config`` is defined, it will be called with the loaded
    ``Config`` instance. This gives callers the opportunity to validate that a
    config is correct. The called function should exit if the config is not
    proper.
    """
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument('config', help='Path to config file to load')
    parser.add_argument('--skip', action='store_true',
                        help='Skip the consuming of the next message then exit')
    args = parser.parse_args()

    config = Config(filename=args.config)

    if validate_config:
        validate_config(config)

    group = config.c.get(config_section, 'group')
    topic = config.c.get(config_section, 'topic')

    root = logging.getLogger()
    handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter('%(name)s %(message)s')
    handler.setFormatter(formatter)
    root.addHandler(handler)

    # hglib will use 'hg' which relies on PATH being correct. Since we're
    # running from a virtualenv, PATH may not be set unless the virtualenv
    # is activated. Overwrite the hglib defaults with a value from the config.
    hglib.HGPATH = config.hg_path

    client = config.get_client_from_section(config_section, timeout=5)

    with Consumer(client, group, topic, partitions=None) as consumer:
        if args.skip:
            r = consumer.get_message()
            if not r:
                print('no message available; nothing to skip')
                sys.exit(1)

            partition = r[0]

            try:
                message_type = r[2]['name']
            except Exception:
                message_type = 'UNKNOWN'

            consumer.commit(partitions=[partition])
            print('skipped %s message in partition %d for group %s' % (
                message_type, partition, group))
            sys.exit(0)

        cbkwargs = {
            'config': config,
        }

        res = run_in_loop(logger, consume_one, config=config, consumer=consumer,
                          cb=cb, cbkwargs=cbkwargs)

    logger.warn('process exiting code %s' % res)
    sys.exit(res)
