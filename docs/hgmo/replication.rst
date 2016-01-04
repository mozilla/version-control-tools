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

* Kafka is a distributed system and can survive a failure in a single node
  (no single point of failure).
* Clients can robustly and independently store the last fetch offset. This
  allows independent replication mirrors.
* Kafka can provide delivery guarantees matching what is desired (order
  preserving, no message loss for acknowledged writes).
* It's fast and battle tested by a lot of notable companies.

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

On each mirror, a daemon is watching the Kafka topic. When a new message
is written, it reacts to it. This typically involves applying data or
performing some action in reaction to an upstream event.

Each mirror operates independently of the leader. There is no direct
signaling from leader to mirror when new data arrives. Instead, each
consumer/daemon independently reacts to the availability of new data in
Kafka. This reaction occurs practically instantaneously, as clients are
continuously polling and Kafka will send data to *subscribed* clients
as soon as it arrives.

A Kafka cluster requires a quorum of servers in order to acknowledge and
thus accept writes. Pushes to Mercurial will fail if quorum is not
available and the replication event can not be robustly stored.

Each mirror maintains its own offset into the replication log. If a
mirror goes offline for an extended period of time, it will resume
applying the replication log where it left off when it reconnects to
Kafka.

The Kafka topic is partitioned. Data for a particular repository is
consistently routed to a specific partition based on the routing
scheme defined on the server. There exist a pool of consumer processes
on the mirror. Each process consumes exactly 1 partition. This enables
concurrent consumption on clients (as opposed to having 1 process that
consumes 1 message at a time) without having to invent a message
acknowledgement and ordering system in addition to what Kafka supports.

Known Deficiencies
------------------

Shared Replication Log and Sequential Consumption
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Consumer processes can only process 1 event at a time. Events from multiple
repositories are written to a shared replication log. Therefore, replication
of repository X may be waiting on an event in repository Y to finish
processing. This can add unwanted replication latency. Or, if a consuming
processes crashes or gets in an endless loop trying to apply an event,
consuming stalls.

Ideally, each repository would have its own replication event log and
a pool of processes could consume events from any available replication
log. There would need to be locking on consumers to ensure multiple
processes aren't operating on the same repository. Such a system may not
be possible with Kafka since apparently Kafka does not scale to thousands
of topics and/or partitions. Although, hg.mozilla.org might be small enough
for this to work. Alternate message delivery systems could potentially
address this drawback. Although many message delivery systems don't provide
the strong guarantees about delivery and ordering that Kafka does.

Reliance on hg pull
^^^^^^^^^^^^^^^^^^^

Currently, pushing of new changegroup data results in ``hg pull`` being
executed on mirrors. ``hg pull`` is robust and mostly deterministic. However,
it does mean that mirrors must connect to the leader server to perform
the replication. This means the leader's availability is necessary to perform
replication.

A replication system more robust to failure of the leader would store all
data in Kafka. As long as Kafka is up, mirrors would be able to synchronize.
Another benefit of this model is that it would likely be faster: mirrors
would have all to-be-applied data immediately available and wouldn't need
to fetch it from a central server. Keep in mind that fetching large amounts
of data can add significant load on the remote server, especially if
several machines are connecting at once.

Another benefit of having all data in the replication log is that we could
potentially store this *bundle* data in a key-value store (like S3)
and leverage Mercurial's built in mechanism for serving bundles from remote
URLs. The Mercurial server would essentially serve ``hg pull`` requests by
telling clients to fetch data from a scalable, possibly distributed
key-value store (such as a CDN).

A benefit of relying on ``hg pull`` based replication is it is simple:
we don't need to reinvent Mercurial data storage. If we stop using ``hg
pull``, various types of data updates potentially fall through the cracks,
especially if 3rd party extensions are involved. Also, storing data in
the replication log could explode the size of the replication log, leading
to its own scaling challenges.

Inconsistency Window on Mirrors
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Mirrors replicate independently. And data applied by mirrors is available
immediately. Therefore, there is a window (hopefully small) where mirrors
have inconsistent state of a repository.

If 2 mirrors are behind the same load balancer and requests are randomly
routed to each of the mirrors, there is a chance a client may encounter
inconsistent state. For example, a client may poll the pushlog to see
what changesets are available then initiate a ``hg pull -r <rev>`` to
fetch a just-pushed changeset. The pushlog from an in sync mirror may
expose the changeset. But the ``hg pull`` hits an out-of-date mirror and
is unable to find the requested changeset.

There are a few potential mechanisms to rectify this problem.

Mirrors could use shared storage. Mercurial's built-in transaction semantics
ensure that clients don't read data that hasn't been fully committed yet.
This is done at the filesystem level so any networked filesystem (like
NFS) that honors atomic file moves should enable consistent state to be
exposed to multiple consumers. However, networked filesystems have their
own set of problems, including performance and possibly single points of
failure. Not all environments are able to support networked filesystems
either.

A potential (and yet unexplored) solution leverages ZooKeeper and
Mercurial's *filtered repository* mechanism. Mercurial's repository
access layer goes through a *filter* that can hide changesets from the
consumer. This is frequently encountered in the context of obsolescence
markers: obsolescence markers hide changesets from normal view. However,
the changesets can still be accessed via the *unfiltered* view, which can
be accessed by calling a ``hg`` command with the ``--hidden`` argument.

It might be possible to store the set of fully replicated heads for a
given repository in ZooKeeper. When a request comes in, we look up which
heads have been fully replicated and only expose changesets up to that
point, even if the local repository has additional data available.

We would like to avoid an operational dependency on ZooKeeper (and Kafka)
for repository read requests. (Currently, reads have no direct dependency
on the availability of the ZooKeeper and Kafka clusters and we'd like to
keep it this way so points of failure are minimized.) Figuring out how
to track replicated heads in ZooKeeper so mirrors can expose consistent
state could potentially introduce a read-time dependency.

Related to this problem of inconsistent state of mirrors is knowing
when to remove a failing mirror from service. If a mirror encounters a
catastrophic failure of its replication mechanism but the Mercurial server
is still functioning, we would ideally detect when the mirror is drifting
out of sync and remove it from the pool of mirrors so clients don't
encounter inconsistent state across the mirror pool. This sounds like
an obvious thing to do. But automatically removing machines can be
dangerous, as being too liberal in yanking machines from service could
result in removing machines necessary to service current load. When you
consider that replication issues tend to occur during periods of high
load, you can imagine what bad situations automatic decisions could get us
in. Extreme care must be practiced when going down this road.

Data Loss
^^^^^^^^^

Data loss can occur in a few scenarios.

Depending on what data is changed in the push, a single push may result
in multiple replication messages being sent. For example, there could be
a changegroup message and a pushkey message. The messages aren't written
to Kafka as an atomic unit. Therefore, it's possible for 1 message to
succeed, the cluster to fail, and the next message to fail, leaving the
replication log in an inconsistent state.

In addition, messages aren't sent until *after* Mercurial closes the
transaction committing data to the repository. It's therefore possible
for the transaction to succeed but the message send to fail.

Both scenarios are mitigated by writing a no-op *heartbeat* message into
the replication log as one of the final steps before transaction close.
If this heartbeat can't be send, the transaction is aborted. The
reasoning here is that by testing the replication log before closing the
transaction, we have a pretty good indication whether the replication
log will be writeable after transaction close. However, there is still
a window for failure.

In the future, we should write a single replication event to Kafka for
each push (requires bundle2 on the client) or write events to Kafka as a
single unit (if that's even supported). We should also support rolling
back the previous transaction in Mercurial if the post transaction
close message(s) fails to write.

Comparison to Legacy Replication System
=======================================

* Writing to replication log is synchronous with pushing but actual
  replication is asynchronous. This means that pushes from the perspective
  of clients are much faster.
* Mirrors that are down will not slow down pushes since push operations
  don't directly communicate with mirrors.
* Mirrors that go down will recover and catch up on replication backlog
  when they return to service (as opposed to requiring manual intervention
  to correct).
* Repository creation events will be automatically replicated.
* hgrc changes will be replicated.
* It will be much easier to write tools that key off the replication log
  for performing additional actions (IRC notifications, e-mail notifications,
  Git mirroring, bug updates, etc).
* (Eventually) The window where inconsistent state is exposed on mirrors
  will be shrunk drastically.

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

   [replicationproducer]

   # Kafka host(s) to connect to.
   hosts = localhost:9092

   # Kafka client id
   clientid = 1

   # Kafka topic to write pushed data to
   topic = pushdata

   # How to map local repository paths to partions. You can:
   #
   # * Have a single partition for all repos
   # * Map a single repo to a single partition
   # * Map multiple repos to multiple partitions
   #
   # The partition map is read in sorted order of the key names.
   # Values are <partition>:<regexp>. If the partitions are a comma
   # delimited list of integers, then the repo path will be hashed and
   # routed to the same partition over time. This ensures that all
   # messages for a specific repo are routed to the same partition and
   # thus consumed in a strict first in first out ordering.
   #
   # Map {repos}/foo to partition 0
   # Map everything else to partitions 1, 2, 3, and 4.
   partitionmap.0foo = 0:\{repos\}/foo
   partitionmap.1bar = 1,2,3,4:.*

   # Required acknowledgement for writes. See the Kafka docs. -1 is
   # strongly preferred in order to not lose data.
   reqacks = -1

   # How long (in MS) to wait for acknowledgements on write requests.
   # If a write isn't acknowledged in this time, the write is cancelled
   # and Mercurial rolls back its transaction.
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
