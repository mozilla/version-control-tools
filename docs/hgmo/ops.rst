.. _hgmo_ops:

=================
Operational Guide
=================

Deploying to hg.mozilla.org
===========================

All code running on the servers behind hg.mozilla.org is in the
version-control-tools repository.

Deployment of new code to hg.mozilla.org is performed via an Ansible
playbook defined in the version-control-tools repository. To deploy new
code, simply run::

   $ ./deploy hgmo

.. important::

   Files from your local machine's version-control-tools working copy
   will be installed on servers. Be aware of any local changes you have
   performed, as they might be reflected on the server.

For minor deployments, pre-announcement of changes is not necessary: just do
the deployment. As part of the deployment, an IRC notification will be issued
in #vcs by Ansible.

For major upgrades (upgrading the Mercurial release or other major changes
such as reconfiguring SSH settings or other changes that have a higher chance
of fallout, pre-announcement is highly recommended.

Pre-announcements should be made to
`dev-version-control <mailto:dev-version-control@lists.mozilla.org>`_.

Deployment-time announcements should be made in ``#vcs``. In addition, the
on-duty Sheriff (they will have ``|Sheriffduty`` appended to their IRC nick)
should be notified. Anyone in ``#releng`` with ``|buildduty`` in their IRC
nick should also be notified. Sending an email to ``sheriffs@mozilla.org``
can't also hurt.

If extra caution is warranted, a bug should be filed against the Change Advisory
Board. This board will help you schedule the upgrade work. Details can be found
at https://wiki.mozilla.org/IT/ChangeControl.

Deployment Gotchas
------------------

Not all processes are restarted as part of upgrades. Notably, the ``httpd`` +
WSGI process trees are not restarted. This means that Python or Mercurial
upgrades may not been seen until the next ``httpd`` service restart. For this
reason, deployments of Mercurial upgrades should be followed by manually
restarting ``httpd`` when each server is out of the load balancer.

Restarting httpd/wsgi Processes
-------------------------------

.. note:: this should be codified in an Ansible playbook

If a restart of the ``httpd`` and WSGI process tree is needed, perform the
following:

1. Log in to the Zeus load balancer at https://zlb1.ops.scl3.mozilla.com:9090
2. Find the ``hgweb-http`` pool.
3. Mark as host as ``draining`` then click ``Update``.
4. Poll the *draining* host for active connections by SSHing into the host
   and curling ``http://localhost/server-status?auto``. If you see more than
   1 active connection (the connection performing server-status), repeat until
   it goes away.
5. ``service httpd restart``
6. Put the host back in service in Zeus.
7. Repeat 3 to 6 until done with all hosts.

Forcing a hgweb Repository Re-clone
===================================

It is sometimes desirable to force a re-clone of a repository to each
hgweb node. For example, if a new Mercurial release offers newer
features in the repository store, you may need to perform a fresh clone
in order to *upgrade* the repository on-disk format.

To perform a re-clone of a repository on hgweb nodes, the
``hgmo-reclone-repos`` deploy target can be used::

   $ ./deploy hgmo-reclone-repos mozilla-central releases/mozilla-beta

The underlying Ansible playbook integrates with the load balancers and
will automatically take machines out of service and wait for active
connections to be served before performing a re-clone. The re-clone
should thus complete without any client-perceived downtime.

Repository Mirroring
====================

On mirrors (hgweb machines), replication of a single repository
can be initiated by running ``/usr/local/bin/mirror-pull``. This
script takes the argument of a repository path, relative to its
home on ``hg.mozilla.org``. e.g. ``hgcustom/version-control-tools``.

**It is important to run this script as the hg user.**

Here is how it is typically used::

   sudo -u hg /usr/local/bin/mirror-pull releases/mozilla-beta

On the *hgssh* machines, you can run a single script to have all
mirrors pull. It works the same way and takes an argument that
is the repository's relative path. e.g.::

   /repo/hg/scripts/push-repo.sh hgcustom/version-control-tools

It is safe to run this script as root - it will ``su`` to the correct
user.

If you want to go a level deeper, you can run
``/usr/local/bin/repo-push.sh``. **This script should be executed
as the hg user.** e.g.::

   sudo -u hg /usr/local/bin/repo-push.sh hgcustom/version-control-tools

Creating New Review Repositories
================================

In order to conduct code review in MozReview, a special review repository
must be configured.

Creating new review repositories is simple::

  $ ./deploy mozreview-create-repo

Then, simply enter requested data in the prompts and the review repository
should be created.

.. note::

   This requires root SSH access to reviewboard-hg1.dmz.scl.mozilla.com
   and for the specified Bugzilla account to have admin privileges on
   reviewboard.mozilla.org.

Marking Repositories as Read-only
=================================

Repositories can be marked as read-only. When a repository is read-only,
pushes are denied with a message saying the repository is read-only.

To mark an individual repository as read-only, create a
``.hg/readonlyreason`` file. If the file has content, it will be printed
to the user as the reason the repository is read-only.

To mark all repositories on hg.mozilla.org as read-only, create the
``/etc/mercurial/readonlyreason`` file. If the file has content, it will
be printed to the user.

.. _hgmo_ops_monitoring:

Monitoring and Alerts
=====================

hg.mozilla.org is monitored by Nagios.

check_zookeeper
---------------

check_zookeeper monitors the health of the ZooKeeper ensemble running on
various servers. The check is installed on each server running
ZooKeeper.

The check verifies 2 distinct things: the health of an individual ZooKeeper
node and the overall health of the ZooKeeper ensemble (cluster of nodes).
Both types of checks should be configured where this check is running.

Expected Output
^^^^^^^^^^^^^^^

When everything is functioning as intended, the output of this check
should be::

   zookeeper node and ensemble OK

Failures of Individual Nodes
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

A series of checks will be performed against the individual ZooKeeper
node. The following error conditions are possible:

NODE CRITICAL - not responding "imok": <response>
   The check sent a ``ruok`` request to ZooKeeper and the server failed to
   respond with ``imok``. This typically means the node is in some kind of
   failure state.

NODE CRITICAL - not in read/write mode: <mode>
   The check sent a ``isro`` request to ZooKeeper and the server did not
   respond with ``rw``. This means the server is not accepting writes. This
   typically means the node is in some kind of failure state.

NODE WARNING - average latency higher than expected: <got> > <expected>
   The average latency to service requests since last query is higher than
   the configured limit. This node is possibly under higher-than-expected
   load.

NODE WARNING - open file descriptors above percentage limit: <value>
   The underlying Java process is close to running out of available file
   descriptors.

   We should never see this alert in production.

If any of these node errors is seen, ``#vcs`` should be notified and the
on call person for these servers should be notified.

Failures of Overall Ensemble
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

A series of checks is performed against the ZooKeeper ensemble to check for
overall health. These checks are installed on each server running ZooKeeper
even though the check is seemingly redundant. The reason is each server may
have a different perspective on ensemble state due to things like network
partitions. It is therefore important for each server to perform the check
from its own perspective.

The following error conditions are possible:

ENSEMBLE WARNING - node (HOST) not OK: <state>
   A node in the ZooKeeper ensemble is not returning ``imok`` to an ``ruok``
   request.

   As long as this only occurs on a single node at a time, the overall
   availability of the ZooKeeper ensemble is not compromised: things should
   continue to work without service operation. If the operation of the
   ensemble is compromised, a different error condition with a critical
   failure should be raised.

ENSEMBLE WARNING - socket error connecting to HOST: <error>
   We were unable to speak to a host in the ensemble.

   This error can occur if ZooKeeper is not running on a node it should be
   running on.

   As long as this only occurs on a single node at a time, the overall
   availability of the ZooKeeper ensemble is not compromised.

ENSEMBLE WARNING - node (HOST) is alive but not available
   A ZooKeeper server is running but it isn't healthy.

   This likely only occurs when the ZooKeeper ensemble is not fully available.

ENSEMBLE CRITICAL - unable to find leader node; ensemble likely not writable
   We were unable to identify a leader node in the ZooKeeper ensemble.

   This error almost certainly means the ZooKeeper ensemble is down.

ENSEMBLE WARNING - only have X/Y expected followers
   This warning occurs when one or more nodes in the ZooKeeper ensemble
   isn't present and following the leader node.

   As long as we still have a quorum of nodes in sync with the leader,
   the overall state of the ensemble should not be compromised.

ENSEMBLE WARNING - only have X/Y in sync followers
   This warning occurs when one or more nodes in the ZooKeeper ensemble
   isn't in sync with the leader node.

   This warning likely occurs after a node was restarted or experienced some
   kind of event that caused it to get out of sync.

check_vcsreplicator_lag
-----------------------

``check_vcsreplicator_lag`` monitors the replication log to see if
consumers are in sync.

This check runs on every host that runs the replication log consumer
daemon, which is every *hgweb* machine. The check is only monitoring the
state of the host it runs on.

The replication log consists of N independent partitions. Each partition
is its own log of replication events. There exist N daemon processes
on each consumer host. Each daemon process consumes a specific partition.
Events for any given repository are always routed to the same partition.

Consumers maintain an offset into the replication log marking how many
messages they've consumed. When there are more messages in the log than
the consumer has marked as applied, the log is said to be *lagging*. A
lagging consumer is measured by the count of messages it has failed to
consume and by the elapsed time since the first unconsumed message was
created. Time is the more important lag indicator because the replication
log can contain many small messages that apply instantaneously and thus
don't really constitute a notable lag.

When the replication system is working correctly, messages written by
producers are consumed within milliseconds on consumers. However, some
messages may take several seconds to apply. Consumers do not mark a message
as consumed until it has successfully applied it. Therefore, there is
always a window between event production and marking it as consumed where
consumers are out of sync.

Expected Output
^^^^^^^^^^^^^^^

When a host is fully in sync with the replication log, the check will
output the following::

   OK - 8/8 consumers completely in sync

   OK - partition 0 is completely in sync (X/Y)
   OK - partition 1 is completely in sync (W/Z)
   ...

This prints the count of partitions in the replication log and the
consuming offset of each partition.

When a host has some partitions that are slightly out of sync with the
replication log, we get a slightly different output::

   OK - 2/8 consumers out of sync but within tolerances

   OK - partition 0 is 1 messages behind (0/1)
   OK - partition 0 is 1.232 seconds behind
   OK - partition 1 is completely in sync (32/32)
   ...

Even though consumers are slightly behind replaying the replication log,
the drift is within tolerances, so the check is reporting OK. However,
the state of each partition's lag is printed for forensic purposes.

Warning and Critical Output
^^^^^^^^^^^^^^^^^^^^^^^^^^^

The monitor alerts when the lag of any one partition of the replication
log is too great. As mentioned above, lag is measured in message count
and time since the first unconsumed message was created. Time is the more
important lag indicator.

When a partition/consumer is too far behind, the monitor will issue a
**WARNING** or **CRITICAL** alert depending on how far behind consumers
are. The output will look like::

   WARNING - 2/8 partitions out of sync

   WARNING - partition 0 is 15 messages behind (10/25)
   OK - partition 0 is 5.421 seconds behind
   OK - partition 1 is completely in sync (34/34)
   ...

The first line will contain a summary of all partitions' sync status. The
following lines will print per-partition state.

The check will also emit a warning when there appears to be clock drift
between the producer and the consumer.::

   WARNING - 0/8 partitions out of sync
   OK - partition 0 is completely in sync (25/25)
   WARNING - clock drift of -1.234s between producer and consumer
   OK - partition 1 is completely in sync (34/34)
   ...

Remediation to Consumer Lag
^^^^^^^^^^^^^^^^^^^^^^^^^^^

If everything is functioning properly, a lagging consumer will self
correct on its own: the consumer daemon is just behind (due to high
load, slow network, etc) and it will catch up over time.

In some rare scenarios, there may be a bug in the consumer daemon that
has caused it to crash or enter a endless loop or some such. To check
for this, first look at *supervisor* to see if all the consumer daemons
are running::

   $ supervisorctl status vcsreplicator:*
   vcsreplicator:0    RUNNING   pid 32217, uptime 4 days, 21:59:24
   vcsreplicator:1    RUNNING   pid 32216, uptime 4 days, 21:59:24
   vcsreplicator:2    RUNNING   pid 32219, uptime 4 days, 21:59:23
   vcsreplicator:3    RUNNING   pid 32218, uptime 4 days, 21:59:24
   vcsreplicator:4    RUNNING   pid 32221, uptime 4 days, 21:59:23
   vcsreplicator:5    RUNNING   pid 16430, uptime 4 days, 21:30:44
   vcsreplicator:6    RUNNING   pid 1809, uptime 4 days, 21:50:55
   vcsreplicator:7    RUNNING   pid 14568, uptime 4 days, 21:36:29

If any of the processes aren't in the ``RUNNING`` state, the consumer
for that partition has crashed for some reason. Try to start it back up:

   $ supervisorctl start vcsreplicator:*

You might want to take a look at the logs in ``/var/log/vcsreplicator`` to
make sure the process is happy.

If there are errors starting the consumer process (including if the
consumer process keeps restarting due to crashing applying the next
available message), then we've encountered a scenario that will
require a bit more human involvement.

.. important::

   At this point, it might be a good idea to ping people in #vcs or
   page Developer Services on Call, as they are the domain experts.

If the consumer daemon is stuck in an endless loop trying to apply
the replication log, there are generally two ways out:

1. Fix the condition causing the endless loop.
2. Skip the message.

We don't yet know of correctable conditions causing endless loops. So,
for now the best we can do is skip the message and hope the condition
doesn't come back::

   $ /repo/hg/venv_replication/bin/vcsreplicator-consumer /etc/mercurial/vcsreplicator.ini --skip

.. important::

   Skipping messages could result in the repository replication state
   getting out of whack.

   If this only occurred on a single machine, consider taking the
   machine out of the load balancer until the incident is investigated
   by someone in #vcs.

   If this occurred globally, please raise awareness ASAP.

.. important::

   If you skip a message, please file a bug in
   `Developer Services :: hg.mozilla.org <https://bugzilla.mozilla.org/enter_bug.cgi?product=Developer%20Services&component=Mercurial%3A%20hg.mozilla.org>`_
   with details of the incident so the root cause can be tracked down
   and the underlying bug fixed.
