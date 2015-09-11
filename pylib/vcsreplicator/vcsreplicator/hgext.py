# This software may be used and distributed according to the terms of the
# GNU General Public License version 2 or any later version.

"""Mercurial extension to write replication events into Kafka."""

import kafka.client as kafkaclient
import vcsreplicator.producer as vcsrproducer

from mercurial import util


testedwith = '3.5'


def uisetup(ui):
    # We assume that if the extension is loaded that we want replication
    # support enabled. Validate required config options are present.
    role = ui.config('replication', 'role')
    if not role:
        raise util.Abort('replication.role config option not set')

    if role not in ('producer', 'consumer'):
        raise util.Abort('unsupported value for replication.role: %s' % role,
                         hint='expected "producer" or "consumer"')

    section = 'replication%s' % role
    hosts = ui.configlist(section, 'hosts')
    if not hosts:
        raise util.Abort('%s.hosts config option not set' % section)
    clientid = ui.config(section, 'clientid')
    if not clientid:
        raise util.Abort('%s.clientid config option not set' % section)
    timeout = ui.configint(section, 'connecttimeout', 10)

    if role == 'producer':
        topic = ui.config(section, 'topic')
        if not topic:
            raise util.Abort('%s.topic config option not set' % section)
        partition = ui.configint(section, 'partition', -1)
        if partition == -1:
            raise util.Abort('%s.partition config option not set' % section)
        reqacks = ui.configint(section, 'reqacks', default=999)
        if reqacks not in (-1, 0, 1):
            raise util.Abort('%s.reqacks must be set to -1, 0, or 1' % section)
        acktimeout = ui.configint(section, 'acktimeout')
        if not acktimeout:
            raise util.Abort('%s.acktimeout config option not set' % section)

    class replicatingui(ui.__class__):
        @property
        def replicationproducer(self):
            if not getattr(self, '_replicationproducer', None):
                client = kafkaclient.KafkaClient(hosts, client_id=clientid,
                                                 timeout=timeout)
                self._replicationproducer = vcsrproducer.Producer(
                    client, topic, partition, batch_send=False,
                    req_acks=reqacks, ack_timeout=acktimeout)

            return self._replicationproducer

    ui.__class__ = replicatingui
