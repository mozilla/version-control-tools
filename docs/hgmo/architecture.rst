.. _hgmo_architecture:

============
Architecture
============

hg.mozilla.org is an Internet connected service.

.. blockdiag::

   blockdiag {
       Internet [shape = cloud];
       hg.mozilla.org [shape = box];

       Internet -> hg.mozilla.org;
   }

hg.mozilla.org exposes HTTP and SSH service endpoints all running on standard ports.
Connections to these services connect to a load balancer.

.. nwdiag::

   nwdiag {
       network {
           address = "load balancer";
           HTTP [address = "port 80"];
           HTTPS [address = "port 443"];
           SSH [address = "port 22"];
       }
   }

HTTP requests to port 80 are **always** HTTP 301 redirected to
https://hg.mozilla.org/ and come back in via port 443.

HTTPS connections to port 443 are routed to a pool of read-only mirrors.
We call these the *hgweb* servers.

.. nwdiag::

   nwdiag {
       network {
           address = "HTTPS/443";
           hgweb01;
           hgweb02;
           hgweb03;
           hgweb04;
       }
   }

(Server names are representative.)

Each server is identically configured and behaves like the others. HTTP
connections/requests are routed to any available *hgweb* server.

SSH connections to port 22 are routed to a single *primary* server. There
is a warm standby for the *primary* server that is made active should
the primary server fail. We collectively refer to these as the *hgssh*
servers.

.. nwdiag::

   nwdiag {
       network {
           address = "SSH/22";
           hgssh01 [address = "primary"];
           hgssh02 [address = "failover"];
       }
   }

SSH connections use public key authentication. User access control and
storage of SSH public keys is stored in an LDAP server.

.. blockdiag::

   blockdiag {
       Client -> OpenSSH -> LDAP;
       LDAP [shape = "flowchart.database"];
       OpenSSH [label = "OpenSSH Server"];
   }

An authenticated SSH connection spawns the ``pash.py`` script from
the version-control-tools repository. This script performs additional
checking of the incoming *request* before eventually spawning an ``hg
serve`` process, which allows the Mercurial client to communicate with
a repository on the server.

.. blockdiag::

   blockdiag {
       SSH -> pash.py -> HG;
       HG [label = "hg serve"];
   }

The *hgssh* servers hold the canonical repository data on a network
appliance exporting a mountable read-write filesystem.

.. blockdiag::

   blockdiag {
       hgssh01 -> nfs;
       hgssh02 -> nfs;
       nfs [label = "Network Filesystem"];
   }

All repository write operations are performed via SSH and are handled by
the *primary* *hgssh* server.

Various Mercurial hooks and extensions run on the *hgssh* server when
repository events occur. Some of these verify incoming changes are
acceptable and reject them if not. Others perform actions in reaction
to the incoming change.

In terms of service architecture, the most important action taken in
reaction to pushes is writing events into the replication system.

Repository Replication Mechanism
================================

The *hgweb* and *hgssh* servers comprising the hg.mozilla.org service run
a `Kafka <https://kafka.apache.org/>`_ cluster. Kafka is a distributed message
service. It allows you to publish and consume an ordered stream of messages
with robust consistency and durability guarantees.

The cluster consists of multiple network services all logically behaving
as a single service.

.. nwdiag::

   nwdiag {
       network {
           address = "Kafka";
           node01 [address = "hgssh01"];
           node02 [address = "hgweb01"];
           node03 [address = "hgweb02"];
           node04 [address = "hgweb03"];
           node05 [address = "hgweb04"];
       }
   }

When a repository event occurs, we publish a message into Kafka describing
that change.

For example, when a repository is created:

.. blockdiag::

   blockdiag {
       span_width = 240;
       init [label = "hg init"];
       init -> Kafka [label = "repo-create"];
   }

When a new push occurs:

.. blockdiag::

   blockdiag {
       span_width = 240;
       push [label = "hg push"];
       push -> Kafka [label = "new-changesets"];
   }

The published message contains the repository name and details about the
change that occurred.

We treat publishing to Kafka as a *transaction*: if we cannot write
messages to Kafka, the current repository change operation is prevented
or *rolled back*.

At a lower level, messages are written into 1 of 8 partitions in the
*pushdata* Kafka topic.

.. blockdiag::

   blockdiag {
       producer -> pushdata0;
       producer -> pushdata1;
       producer -> pushdata2;
       producer -> pushdata3;
       producer -> pushdata4;
       producer -> pushdata5;
       producer -> pushdata6;
       producer -> pushdata7;
   }

Each repository deterministically writes to the same partition via a name-based
routing mechanism plus hashing. For example, the *foo* repository may always
write to partition ``1`` but the *bar* repository may always write to
partition ``6``.

Messages published to Kafka topics/partitions are ordered: if message ``A`` is
published before message ``B``, consumers will always see ``A`` before ``B``.

On each *hgweb* server, we run a ``vcsreplicator-consumer`` daemon process bound
to each partition in the *pushdata* Kafka topic. These processes essentially
monitor each partition in the topic for new messages.

.. blockdiag::

   blockdiag {
       producer -> pushdata0 <- vcsreplicator0;
       producer -> pushdata1 <- vcsreplicator1;
       producer -> pushdata2 <- vcsreplicator2;
       producer -> pushdata3 <- vcsreplicator3;
       producer -> pushdata4 <- vcsreplicator4;
       producer -> pushdata5 <- vcsreplicator5;
       producer -> pushdata6 <- vcsreplicator6;
       producer -> pushdata7 <- vcsreplicator7;
   }

When a new message is written to the partition, the consumer reacts to that
message, typically by invoking an ``hg`` process to complete the action.

.. seqdiag::

   seqdiag {
       producer -> pushdata2 [label = "new-repo"];
       pushdata2 <- vcsreplicator2 [label = "new-repo"];
       vcsreplicator2 -> init;
       init [label = "hg init"];
       pushdata2 <-- vcsreplicator2 [label = "ack"];
   }

Sometimes the replicated data is too large to fit in a Kafka
message. In that case, the consumer will connect to the *hgssh*
server to obtain data.

.. seqdiag::

   seqdiag {
       pushdata2 <- vcsreplicator2 [label = "msg"];
       vcsreplicator2 -> hg;
       hg -> hgssh [label = "hg pull"];
       hg <-- hgssh [label = "apply data"];
       pushdata2 <-- vcsreplicator2 [label = "ack"];
   }

Consumers react to new messages within milliseconds of the message being
written. And the same activity is occurring on each *hgweb* server
independently.

.. blockdiag::

   blockdiag {
       producer -> pushdata2 [label = "msg"];
       pushdata2 <- consumer01 [label = "msg"];
       pushdata2 <- consumer02 [label = "msg"];
       pushdata2 <- consumer03 [label = "msg"];
       pushdata2 <- consumer04 [label = "msg"];

       group hgweb01 {
           label = "hgweb01";
           consumer01 -> hg01;
           consumer01 [label = "vcsreplicator2"];
           hg01 [label = "hg"];
       }

       group hgweb02 {
           label = "hgweb02";
           consumer02 -> hg02;
           consumer02 [label = "vcsreplicator2"];
           hg02 [label = "hg"];
       }

       group hgweb03 {
           label = "hgweb03";
           consumer03 -> hg03;
           consumer03 [label = "vcsreplicator2"];
           hg03 [label = "hg"];
       }

       group hgweb04 {
           label = "hgweb04";
           consumer04 -> hg04;
           consumer04 [label = "vcsreplicator2"];
           hg04 [label = "hg"];
       }
   }

When the consumer successfully performs action in reaction to a received
message, it tells Kafka. Once a consumer has acknowledged that it processed
a message, that message will never be delivered to that consumer again.

Consumers typically fully process a repository event / message within a few
seconds. Events corresponding to *big* changes (such as cloning a repository,
large pushes, etc) can take longer - sometimes minutes.

We rely on repository change messages to have deterministic side-effects. i.e.
independent consumers starting in the same state that apply the same stream
of messages should end up in an identical state.

Consumers only process a single message per topic+partition simultaneously.
This is to ensure ordering of messages is adhered to and that no message
is successfully processed more than once (Kafka records message delivery
by recording the consumer's message offset within a logical queue).

This all means that there can be a lag and backlog of messages after the
*hgssh* server produces a Kafka message and the *hgweb* servers apply it.
In addition, there is a window where each *hgweb* server may have slightly
different state of a repository, since each *hgweb* server will consume and
apply messages at different rates.

See :ref:`hgmo_replication` for more on this replication system.

Aggregated Push Data and Notifications
======================================

The primary *hgssh* server runs a service that monitors the consumer state
of the replication service on all *hgweb* consumers. It essentially repeatedly
polls Kafka, asking it for the topic+partition offsets for all known
*hgweb* topic consumers.

When all *hgweb* consumers have acknowledged that they've processed a message,
this service re-publishes that fully consumed message in the *pushdataaggregator*
Kafka topic.

.. seqdiag::

   seqdiag {
       pushdata0 <- consumer01 [label = "msg0"];
       pushdata0 <- consumer02 [label = "msg0"];

       pushdata0 <-- consumer02 [label = "ack"];
       pushdata0 <-- consumer01 [label = "ack"];

       aggregator -> pushdataaggregator [label = "msg0"];
   }

The stream of messages in the *pushdataaggregator* Kafka topic represents
all fully replicated repository changes available on the *hgweb* servers.

Various services on the active primary *hgssh* server consume this aggregate
topic and do things with the messages. One consumer notifies Pulse of repository
changes. Another sends messages to AWS SNS.

.. blockdiag::

   blockdiag {
       pushdataaggregator <- pulsenotifier -> Pulse;
       pushdataaggregator <- snsnotifier -> SNS;
       pulsenotifier [label = "Pulse Notifier"];
       snsnotifier [label = "SNS Notifier"];
   }

See :ref:`hgmo_notification` for more.

From there, various other services not part of the hg.mozilla.org
infrastructure react to events. For example, *pulsebot* creates IRC
notifications, Taskcluster schedules Firefox CI, and Treeherder records
the push.

.. blockdiag::

   blockdiag {
       Pulse <- pulsebot -> IRC;
       Pulse <- Taskcluster -> task;
       Pulse <- Treeherder;
       task [label = "Firefox Decision Task"];
   }

HTTP Repository Serving
=======================

Nearly every consumer of hg.mozilla.org consumes the service via HTTP: only
pushes should be using SSH.

The HTTP service is pretty standard for a Python-based service: there's an HTTP
server running on each *hgweb* server that converts the requests to WSGI and
sends them to a Python process running Mercurial's built-in *hgweb* server.
*hgweb* handles processing the request and generating a response.

*hgweb* serves mixed content types (HTML, JSON, etc) for web browsers and other
agents. In addition, *hgweb* also services Mercurial's custom *wire protocol*
for communicating with Mercurial clients.

When a client executes an ``hg`` command that needs to talk to hg.mozilla.org,
the client process establishes an HTTP connection with hg.mozilla.org and
issues commands to a repository there via HTTP. Run
``hg help internals.wireproto`` for details of how this works.

Clone Offload
-------------

In order to alleviate server-side CPU and network load, frequently accessed
repositories on hg.mozilla.org use Mercurial's *clone bundles* feature so
``hg clone`` operations download most repository data from a pre-generated
static *bundle* file hosted on a scalable HTTP server.

Most Mercurial clients will fetch a bundle from the CloudFront CDN.

.. seqdiag::

   seqdiag {
       hg [label = "Mercurial Client"];
       hgweb [label = "hg.mozilla.org"];

       hg -> hgweb [label = "GET /mozilla-unified?cmd=clonebundles"];
       hg <-- hgweb [label = "available pre-generated bundles"];
       hg -> CDN [label = "GET mozilla-unified/bundle.hg"];
       hg <-- CDN [label = "apply repository data"];
       hg -> hgweb [label = "pull recent repository data"];
       hg <-- hgweb [label = "apply recent data"];
   }

If the client can't connect to CloudFront (requires SNI) or if the
client is connecting from an AWS IP belonging to an AWS region where
we have an S3 bucket containing repository data, the client will
connect to S3 instead.

.. seqdiag::

   seqdiag {
       hg [label = "Mercurial Client"];
       hgweb [label = "hg.mozilla.org"];

       hg -> hgweb [label = "GET /mozilla-unified?cmd=clonebundles"];
       hg <-- hgweb [label = "available pre-generated bundles"];
       hg -> S3 [label = "GET mozilla-unified/bundle.hg"];
       hg <-- S3 [label = "apply repository data"];
       hg -> hgweb [label = "pull recent repository data"];
       hg <-- hgweb [label = "apply recent data"];
   }

Offloading the bulk of expensive ``hg clone`` operations to pre-generated
files hosted on highly scalable services results in faster clones for
clients and drastically reduces the server requirements for the hg.mozilla.org
service.

See :ref:`hgmo_bundleclone` and the
`Cloning from S3 <http://gregoryszorc.com/blog/2015/07/08/cloning-from-s3/>`_
blog post for more on *clone bundles*.
