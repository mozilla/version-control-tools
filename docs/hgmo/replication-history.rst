.. _hgmo_replication_history:

==============================
History of Replication Systems
==============================

This document aims to describe the historical approaches to repository
replication used by hg.mozilla.org. Reading this document should leave
readers with an understanding of what replication approaches were used,
what worked, what didn't, why we switched strategies, etc.

Shared Filesystem / No Replication
==================================

When hg.mozilla.org was initially deployed, the SSH and HTTP servers
used a shared filesystem via NFSv3. This was architecturally simple.
All writes were available atomically on the read-only HTTP servers.

However, it suffered from a few serious limitations.

First, Mercurial makes heavy use of multiple files for repository
storage. This I/O access model combined with NFS's overhead for I/O
operations meant that many Mercurial operations were slow. Therefore
hg.mozilla.org was slow. Fixing this would require overhauling how
Mercurial repository storage worked. Not an easy endeavor!

Second, the lack of a writable filesystem meant that Mercurial could
not populate various repository cache files and this made some
Mercurial operations very slow. (The HTTP servers mounted the filesystem
read-only for security reasons.) This issue could have been worked around
by writing a Mercurial extension to store cache files in a separate
location than ``.hg/cache``. However, we never did so. Another workaround
would have been to populate all the necessary caches on the SSH server at
push time so an HTTP server wouldn't need to write caches since they
were already up-to-date.

Because NFS was making read-only operations on the HTTP servers
substantially slower than they had the potential to be, we decided to
have the HTTP servers store repositories on their local filesystem
and to use a replication system to keep everything in sync.

Push-Time Synchronous Replication
=================================

The push-time replication system was our first replication system. It
was very crude yet surprisingly effective:

1. A hook fired during the ``changegroup`` and ``pushkey`` hooks as part
   of ``hg push`` operations.
2. This hook executed the ``repo-push.sh`` script, which iterated through
   all mirrors and effectively ran ``ssh -l hg <mirror> <repo>``.
3. On each mirror, the SSH session effectively ran the ``mirror-pull``
   scripts. This scripts essentially ran
   ``hg pull ssh://hg.mozilla.org/<repo>``.

Each mirror performed its replication in parallel. So the number of
mirrors could be scaled without increasing replication time proportionally.

Replication was performed synchronously with the push. So, the client's
``hg push`` command doesn't finish until all mirrors had completed their
replication. This added a few seconds of latency to pushes.

There were several downsides with this replication method:

* Replication was synchronous with push, adding latency. This was felt
  most notably on the Try repository, which took 9-15s to replicate.
  Other repositories typically would take 1-8s.
* If a mirror was slow, it was a long pole and slowed down replication for
  the push, adding yet more latency to the push.
* If a mirror was down, the system was not intelligent enough to
  automatically remove the mirror from the mirrors list. The master would
  retry several times before failing. This added latency to pushes.
* If a mirror was removed from the replication system, it didn't re-sync
  when it came back online. Instead, it needed to be manually re-synced by
  running a script. If a server rebooted for no reason, it could become out
  of sync and someone may or may not re-sync it promptly.
* Each mirror synced and subsequently exposed data at different times.
  There was a window during replication where mirror A would advertise
  data that mirror B did not yet have. This could lead to clients seeing
  inconsistent repository state due to hitting different servers behind
  the load balancer.

In addition:

* There was no mechanism for replicating repository creation or deletion
  events.
* This was no mechanism for replicating hgrc changes.
* This replication system was optimized for a low-latency,
  high-availability intra-datacenter environment and wouldn't work well
  with a future, globally distributed hg.mozilla.org service (which would
  be far more prone to network events such as loss of connectivity).

Despite all these downsides, the legacy replication system was
surprisingly effective. Mirrors getting out of sync was rare.
Historically the largest problem was the increased push latency due
to synchronous replication.

Kafka-Based Replication System
==============================

We wanted a replication system with fewer deficiencies than the
push-time synchronous replication system described in the section above.
Notably, we wanted:

* Replication to be asynchronous with the ``hg push`` operation so people
  wouldn't have to wait as long for their operation to complete.
* Mirrors that were down or slow wouldn't slow down ``hg push`` operations.
* Mirrors that went down would recover and catch up on replication backlog
  automatically when they return to service.
* Repository creation and deletion events could be replicated.
* hgrc changes could be replicated.
* The window of inconsistency across the HTTP servers would be reduced.

We devised a replication system built on top of message queues backed by
Apache Kafka to implement such a system.

This system is described in detail at
:ref:`hgmo_replication`.

Essentially, Kafka provides a distributed transaction log. During ``hg push``
operations, the server writes messages into Kafka describing the changes that
were made to the repository. Daemons on mirrors react to new messages within
milliseconds, triggering the replication of repository data. The stream of
messages is ordered and consumers record their consume offset. This allows
consumers to go offline and resume replication at the last consumed offset
when they come back online.
