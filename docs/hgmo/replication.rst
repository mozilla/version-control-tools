.. _hgmo_replication:

===========
Replication
===========

As described at :ref:`hgmo_architecture`, ``hg.mozilla.org`` consists of
a read/write master server available via SSH and a set of read-only
mirrors available over HTTP. As changes are pushed to the master server,
they are replicated to the read-only mirrors.

Legacy Replication System
=========================

The legacy replication system is very crude yet surprisingly effective:

1. ``mozhghooks.replicate`` hook fires during *changegroup* and
   *pushkey* hooks as part of push operations.
2. ``/usr/local/bin/repo-push.sh`` is invoked. This script iterates
   through all mirrors and effectively runs ``ssh -l hg <mirror>
   <repo>``.
3. On each mirror, the SSH session effectively runs
   ``/usr/local/bin/mirror-pull <repo>``. The ``mirror-pull`` script
   then typically performs a ``hg pull ssh://<master>/<repo>``.

Each mirror performs its replication in parallel. So, the number of
mirrors can be scaled without increasing mirror time proportionally.

Replication is performed synchronously with the push. So, the client's
``hg push`` command doesn't finish until replication finishes. This adds
latency to pushes.

There are several downsides with this replication method:

* Replication is synchronous with push, adding latency. This is felt
  most notably on the Try repository, which takes 9-15s to replicate.
  Other repositories typically take 1-8s.
* If a mirror is slow, it is a long pole and slows down replication for
  the push, adding yet more latency to the push.
* If a mirror is down, the system is not intelligent enough to
  automatically remove the mirror from the mirrors list. The master will
  retry several times before failing. This adds latency to pushes.
* If a mirror is removed from the replication system, it doesn't re-sync
  when it comes back online. Instead, it must be manually re-synced by
  running a script. If a server reboots for no reason, it can become out
  of sync and someone may or may not re-sync it promptly.
* Each mirror syncs and subsequently exposes data at different times.
  There is a window during replication where mirror A will advertise
  data that mirror B does not yet have. This can lead to clients seeing
  inconsistent repository state due to hitting different servers behind
  the load balancer.

In addition:

* There is no mechanism for replicating repository creation or deletion
  events.
* This is no mechanism for replicating hgrc changes.
* This replication system is optimized for a low-latency,
  high-availability intra-datacenter environment and won't work well
  with a future, globally distributed hg.mozilla.org service (which will
  be far more prone to network events such as loss of connectivity).

Despite all these downsides, the legacy replication system is
surprisingly effective. Mirrors getting out of sync is rare.
Historically the largest problem has been the increased push latency due
to synchronous replication.

VCSReplicator Introduction
==========================

Version Control System Replicator (vcsreplicator - ``pylib/vcsreplicator``) is
a modern system for replicating version control data.

vcsreplicator is built on top of a distributed transaction log. When changes
(typically pushes) are performed, an event is written to the log. Downstream
consumers read from the log (hopefully in near real time) and replay changes
that were made upstream.

The distributed transaction log is built on top of
`Apache Kafka <https://kafka.apache.org/>`. Unlike other queueing and message
delivery systems (such as AMQP/RabbitMQ), Kafka provides guarantees that
satisfy our requirements. Notably:

* Kafka stores data to local disk and is durable against single node failure.
* Clients can robustly and independently store the last fetch offset. This
  allows independent replication mirrors.
* Kafka can provide delivery guarantees matching what is desired.
* It's fast and battle tested.

For more on the subject of distributed transaction logs, please read
`this excellent article from the people behind Kafka <https://engineering.linkedin.com/distributed-systems/log-what-every-software-engineer-should-know-about-real-time-datas-unifying>`_.

vcsreplicator is currently designed to replicate changes from a single
*leader* Mercurial server to several, independent *mirror* servers. It
supports replicating:

* changegroup data
* pushkey data (bookmarks, phases, obsolescence markers, etc)
* hgrc config files
* repository creation

How it Works
============

A Kafka topic for holding Mercurial replication data is created. A
Mercurial extension is installed on the leader server (the server where
writes go). When data is written to a Mercurial repository, that data or
metadata is written into Kafka.

On each mirror, a daemon is watching the Kafka topic. When it sees a
replication event, it reacts to it and applies the data or performs
actions that will apply the data.

Each mirror operates independently of the leader. There is no direct
signaling from leader to mirror when new data arrives. Instead, each
consumer/daemon independently reacts to the availability of new data in
Kafka. This reaction occurs practically instantaneously.

A Kafka cluster requires a quorum of servers in order to acknowledge and
thus accept writes. Pushes to Mercurial will fail if quorum is not
available and the replication event can not be robustly stored.

Each mirror maintains its own offset into the replication log. If a
mirror goes offline for an extended period of time, it will resume
applying the replication log where it left off when it reconnects to
Kafka.

Installation and Configuring
============================

vcsreplicator requires Python 2.7+, access to an Apache Kafka cluster, and
an existing Mercurial server or repository.

For now, we assume you have a Kafka cluster configured. (We'll write the docs
eventually.)

Mercurial Extension Installation
--------------------------------

On a machine that is to produce or consume replication events, you will need
to install the vcsreplicator Python package::

   $ pip install /version-control-tools/pylib/vcsreplicator

On the leader machine, you will need to install a Mercurial extension.
Assuming this repository is checked out in ``/version-control-tools``, you
will need the following in an hgrc file (either the global one or one
inside a repository you want replicated)::

   [extensions]
   # Load it by Python module (assuming it is in sys.path for the
   # Mercurial server processes)
   vcsreplicator.hgext =

   # Load it by path.
   vcsreplicator = /path/to/vcsreplicator/hgext.py

Producer hgrc Config
--------------------

You'll need to configure your hgrc file to work with vcsreplicator::

   # Tell vcsreplicator that we are a producer node (performing writes).
   [replication]
   role = producer

   # Configure the producer.
   [replicationproducer]

   # Kafka host(s) to connect to.
   hosts = localhost:9092

   # Kafka client id
   clientid = 1

   # Kafka topic to write pushed data to
   topic = pushdata

   # Partition to write data to.
   partition = 0

   # Required acknowledgement for writes. See the Kafka docs. -1 is
   # strongly preferred in order to not lose data.
   reqacks = -1

   # How long (in MS) to wait for acknowledgements on write requests.
   acktimeout = 10000

   # Normalize local filesystem paths for representation on the wire.
   # This enables leader and mirrors to have different local filesystem
   # paths.
   [replicationpathrewrites]
   /var/repos/ = {repos}/

Consumer Config File
--------------------

The consumer daemon requires a config file.

The ``[consumer]`` section defines how to connect to Kafka to receive
events. You typically only need to define it on the follower nodes.
It contains the following variables:

hosts
   Comma delimited list of ``host:port`` strings indicating Kafka hosts.
client_id
   Unique identifier for this client.
connect_timeout
   Timeout in milliseconds for connecting to Kafka.
topic
   Kafka topic to consume. Should match producer's config.
group
   Kafka group the client is part of.

   **You should define this to a unique value.**

The ``[path_rewrites]`` section defines mappings for how local filesystem
paths are normalized for storage in log messages and vice-versa.

This section is not required. Presence of this section is used to abstract
storage-level implementation details and to allow messages to define
a repository without having to use local filesystem paths. It's best
to explain by example. e.g.::

   [path_rewrites]
   /repos/hg/ = {hg}/

If a replication producer produces an event related to a repository under
``/repos/hg/`` - let's say ``/repos/hg/my-repo``, it will normalize the
path in the replication event to ``{hg}/my-repo``. You could add a
corresponding entry in the config of the follower node::

   [path_rewrites]
   {hg}/ = /repos/mirrors/hg/

When the consumer sees ``{hg}/my-repo``, it will expand it to
``/repos/mirrors/hg/my-repo``.

Path rewrites are very simple. We take the input string and match against
registered rewrites in the order they were defined. Only a leading string
search is performed - we don't match if the first character is different.
Also, the match is case-insensitive (due to presence of case-insensitive
filesystems that may report different path casing) but case-preserving. If
you have camelCase in your repository name, it will be preserved.

The ``[pull_url_rewrites]`` section is used to map repository paths
from log messages into URLs suitable for pulling from the leader.
They work very similarly to ``[path_rewrites]``.

The use case of this section is that it allows consumers to construct
URLs to the leader repositories at message processing time rather than
message produce time. Since URLs may change over time (don't tell Roy T.
Fielding) and since the log may be persisted and replayed months or even
years later, there needs to be an abstraction to redefine the location
of a repository later.

.. note::

   The fact that consumers perform an ``hg pull`` and need URLs to pull
   from is unfortunate. Ideally all repository data would be
   self-contained within the log itself. Look for a future feature
   addition to vcsreplicator to provide self-contained logs.

Current and Planned Project State
=================================

The project is currently in its early stages. The immediate goal of the
project is to take control of replication for hg.mozilla.org, replacing
the synchronous-with-push and non-robust replication described above. The
existing solution is prone to many failures, so fortunately the bar is set
low.
