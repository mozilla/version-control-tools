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
5. ``systemctl restart httpd.service``
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

The replication/mirroring of repositories is initiated on the master/SSH
server. An event is written into a distributed replication log and it is
replayed on all available mirrors. See :ref:`hgmo_replication` for more.

Most repository interactions result in replication occurring automatically.
In a few scenarios, you'll need to manually trigger replication.

The ``vcsreplicator`` Mercurial extension defines commands for creating
replication messages. For a full list of available commands run
``hg help -r vcsreplicator``. The following commands are common.

hg replicatehgrc
   Replicate the hgrc file for the repository. The ``.hg/hgrc`` file will
   effectively be copied to mirrors verbatim.

hg replicatesync
   Force mirrors to synchronize against the master. This ensures the repo
   is present on mirrors, the hgrc is in sync, and all repository data from
   the master is present.

   Run this if mirrors ever get out of sync with the master. It should be
   harmless to run this on any repo at any time.

.. important::

   You will need to run ``/var/hg/venv_tools/bin/hg`` instead of
   ``/usr/bin/hg`` so Python package dependencies required for
   replication are loaded.

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

Stripping Changesets from a Review Repository
=============================================

It is sometimes necessary to remove traces of a changeset from a **review**
repository. This can be accomplished by running a command from a shell on
a reviewboard-hg server::

   $ cd /repo/hg/mozilla/<repo>
   $ sudo -u hg /var/hg/venv_pash/bin/hg --config extensions.strip= strip -r <revision>

.. important::

   If the ``hg`` from the ``pash`` virtualenv isn't used, the pushlog may get
   corrupted when running ``hg strip``.

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

Retiring Repositories
=====================

Users can :ref:`delete their own repositories <hgmo_delete_user_repo>` - this section applies only to
non-user repositories.

Convention is to retire (aka delete) repositories by moving them out of
the user accessible spaces on the master and deleting from webheads.

This can be done via ansible playbook in the version-control-tools
repository::

  $ cd ansible
  $ ansible-playbook -i hosts -e repo=relative/path/on/server hgmo-retire-repo.yml

Managing Repository Hooks
=========================

It is somewhat common to have to update hooks on various repositories.

The procedure for doing this is pretty simple:

1. Update a ``.hg/hgrc`` file on the SSH master
2. Replicate hgrc to mirrors

Generally speaking, ``sudo vim`` to edit ``.hg/hgrc`` files is sufficient.
Ideally, you should use ``sudo -u hg vim .hg/hgrc``.

To replicate hgrc changes to mirrors after updating an hgrc, simply run::

   $ /var/hg/venv_tools/bin/hg replicatehgrc

.. note::

   ``hg replicatehgrc`` operates on the repo in the current directory.

The definition of hooks is somewhat inconsistent. Generally speaking, hook
entries are cargo culted from another repo.

Try Head Management
===================

The Try repository continuously grows new heads as people push to it.
There are some version control operations that scale with the number of
heads. This means that the repository gets slower as the number of heads
increases.

To work around this slowness, we periodically remove old heads. We do this
by performing dummy merges. The procedure for this is as follows::

   # Clone the Try repo. This will be very slow unless --uncompressed is used.
   hg clone --uncompressed -U https://hg.mozilla.org/try
   cd try
   # Verify heads to merge (this could take a while on first run)
   hg log -r 'head() and branch(default) and not public()'
   # Capture the list of heads to merge
   hg log -r 'head() and branch(default) and not public()' -T '{node}\n' > heads
   # Update the working directory to the revision to be merged into. A recent
   # mozilla-central revision is typically fine.
   hg up <revision>
   # Do the merge by invoking `hg debugsetparents` repeatedly
   for p2 in `cat heads`; do echo $p2; hg debugsetparents . $p2; hg commit -m 'Merge try head'; done

Clonebundles Management
=======================

Various repositories have their content *snapshotted* and uploaded to S3.
These snapshots (*bundles* in Mercurial parlance) are advertised via the
Mercurial server to clients and are used to seed initial clones. See
:ref:`hgmo_bundleclone` for more.

From an operational perspective, bundle generation is triggered by the
``hg-bundle-generate.service`` and ``hg-bundle-generate.timer`` systemd
units on the master server. This essentially runs the
``generate-hg-s3-bundles`` script. Its configuration lives in the script
itself as well as ``/repo/hg/bundles/repos`` (which lists the repos to
operate on and their bundle generation settings).

The critical output of periodic bundle generation are the objects uploaded
to S3 (to multiple buckets in various AWS regions) and the advertisement
of these URLs in per-repo ``.hg/clonebundles.manifest`` files. Essentially
for each repo:

1. Bundles are generated
2. Bundles are uploaded to multiple S3 buckets
3. ``clonebundles.manifest`` is updated to advertise newly-uploaded URLs
4. ``clonebundles.manifest`` is replicated from hgssh to hgweb mirrors
5. Clients access ``clonebundles.manifest`` as part of ``hg clone`` and
   start requesting referenced URLs.

If bundle generation fails, it isn't the end of the world: the old
bundles just aren't as up to date as they could be.

.. important::

   The S3 buckets have automatic 7 day expiration of objects. The
   assumption is that bundle generation completes successfully at
   least once a week. If bundle generation doesn't run for 7 days,
   the objects referenced in ``clonebundles.manifest`` files will
   expire and clients will encounter HTTP 404 errors.

In the event that a bundle is *corrupted*, manual intervention may be
required to mitigate to problem.

As a convenience, a backup of the ``.hg/clonebundles.manifest`` file
is created during bundle generation. It lives at
``.hg/clonebundles.manifest.old``. If a new bundle is corrupt but an
old one is valid, the mitigation is to restore from backup::

   $ cp .hg/clonebundles.manifest.old .hg/clonebundles.manifest
   $ /var/hg/venv_tools/bin/hg replicatesync

If a single bundle or type of bundle is corrupted or causing problems,
it can be removed from the ``clonebundles.manifest`` file so clients
stop seeing it.

Inside the ``clonebundles.manifest`` file are *N* types of bundles
uploaded to *M* S3 buckets (plus a CDN URL). The bundle types can be
identified by the ``BUNDLESPEC`` value of each entry. For example,
if *stream clone* bundles are causing problems, the entries with
a ``BUNDLESPEC`` containing ``none-packed`` could be removed.

.. danger::

   Removing entries from a ``clonebundles.manifest`` can be dangerous.

   The removal of entries could shift a lot of traffic from S3/CDN to
   the hgweb servers themselves - possibly overloading them.

   The removal of a particular entry type could have performance
   implications for Firefox CI. For example, removing *stream clone*
   bundles will make ``hg clone`` take several minutes longer. This
   is often acceptable as a short-term workaround and is preferred to
   removing *clone bundles* entirely.

.. important::

   If modifying a ``.hg/clonebundles.manifest`` file, remember to run
   ``/repo/hg/venv_tools/bin/hg replicatesync`` to trigger the replication
   of that file to hgweb mirrors. Otherwise clients won't see the changes!

Corrupted fncache File
======================

In rare circumstances, a ``.hg/store/fncache`` file can become corrupt.
This file is essentially a cache of all known files in the ``.hg/store``
directory tree.

If this file becomes corrupt, symptoms often manifest as *stream clones*
being unable to find a file. e.g. during working directory update there
will be an error::

   abort: No such file or directory: '<path>'

You can test the theory that the fncache file is corrupt by grepping for
the missing path in the ``.hg/store/fncache`` file. There should be a
``<path>.i`` entry in the ``fncache`` file. If it is missing, the fncache
file is corrupt.

To rebuild the ``fncache`` file::

   $ sudo -u <user> /var/hg/venv_tools/bin/hg -R <repo> debugrebuildfncache

Where ``<user>`` is the user that owns the repo (typically ``hg``) and
``<repo>`` is the local filesystem path to the repo to repair.

``hg debugrebuildfncache`` should be harmless to run at any time. Worst
case, it effectively no-ops. If you are paranoid. make a backup copy of
``.hg/store/fncache`` before running the command.

.. important::

   Under no circumstances should ``.hg/store/fncache`` be removed or
   altered by hand. Doing so may result in further repository damage.

Mirrors in ``pushdataaggregator_groups`` File
=============================================

On the SSH servers, the ``/etc/mercurial/pushdataaggregator_groups`` file
lists all hgweb mirrors that must have acknowledged replication of a message
before that message is re-published to ``replicatedpushdata`` Kafka topic.
This topic is then used to publish events to Pulse, SNS, etc.

When adding or removing hgweb machines from active service, this file
needs to be **manually** updated to reflect the current set of active
mirrors.

If an hgweb machine is removed and the ``pushdataaggregator_groups`` file
is not updated, messages won't be re-published to the ``replicatedpushdata``
Kafka topic. This should eventually result in an alert for lag of that
Kafka topic.

If an hgweb machine is added and the ``pushdataaggregator_groups`` file
is not updated, messages could be re-published to the ``replicatedpushdata``
Kafka topic before the message has been acknowledged by all replicas. This
could result in clients seeing inconsistent repository state depending on
which hgweb server they access.

.. _hgmo_ops_monitoring:

SSH Server Services
===================

This section describes relevant services running on the SSH servers.

An SSH server can be in 1 of 2 states: *master* or *standby*. At any one
time, only a single server should be in the *master* state.

Some services always run on the SSH servers. Some services only run on
the active master.

The *standby* server is in a state where it is ready to become the
master at any time (such as if the master crashes).

.. important::

   The services that run on the active master are designed to only have
   a single global instance. Running multiple instances of these services
   can result in undefined behavior or event data corruption.

Master Server Management
------------------------

The current active master server is denoted by the presence of a
``/repo/hg/master.<hostname>`` file. e.g. the presence of
``/repo/hg/master.hgssh4.dmz.scl3.mozilla.com`` indicates that
``hgssh4.dmz.scl3.mozilla.com`` is the active master.

All services that should have only a single instance (running on the
master) have systemd unit configs that prevent the unit from starting
if the ``master.<hostname>`` file for the current server does not exist.
So, as long as only a single ``master.<hostname>`` file exists, it should
not be possible to start these services on more than one server.

The ``hg-master.target`` systemd unit provides a common target for
starting and stopping all systemd units that should only be running on the
active master server. The unit only starts if the
``/repo/hg/master.<hostname>`` file is present.

.. note::

   The ``hg-master.target`` unit only tracks units specific to the master.
   Services like the sshd daemon processing Mercurial connections are
   always running and aren't tied to ``hg-master.target``.

The ``/repo/hg/master.<hostname>`` file is monitored every few seconds by
the ``hg-master-monitor.timer`` and associated
``/var/hg/version-control-tools/scripts/hg-master-start-stop`` script.
This script looks at the status of the ``/repo/hg/master.<hostname>``
file and the ``hg-master.target`` unit and reconciles the state of
``hg-master.target`` with what is wanted.

For example, if ``/repo/hg/master.hgssh4.dmz.scl3.mozilla.com`` exists
and ``hg-master.target`` isn't active, ``hg-master-start-stop`` will
start ``hg-master.target``. Similarly, if
``/repo/hg/master.hgssh4.dmz.scl3.mozilla.com`` is deleted,
``hg-master-start-stop`` will ensure ``hg-master.target`` (and all
associated services by extension) are stopped.

So, the process for transitioning master-only services from one machine
to another is to delete one ``master.<hostname>`` file then create a
new ``master.<hostname>`` for the new master.

.. important::

   Since ``hg-master-monitor.timer`` only fires every few seconds and
   stopping services may take several seconds, one should wait at least
   60s between removing one ``master.<hostname>`` file and creating a
   new one for a server server. This limitation could be improved with
   more advanced service state tracking.

sshd_hg.service
---------------

This systemd service provides the SSH server for accepting external SSH
connections that connect to Mercurial.

This is different from the system's SSH service (``sshd.service``). The
differences from a typical SSH service are as follows:

* The service is running on port 222 (not port 22)
* SSH authorized keys are looked up in LDAP (not using the system auth)
* All logins are processed via ``pash``, a custom Python script that
  dispatches to Mercurial or performs other adminstrative tasks.

This service should always be running on all servers, even if they aren't
the master. This means that ``hg-master.target`` does not control this
service.

hg-bundle-generate.timer and hg-bundle-generate.service
-------------------------------------------------------

These systemd units are responsible for creating Mercurial bundles for
popular repositories and uploading them to S3. The bundles it produces
are also available on a CDN at https://hg.cdn.mozilla.net/.

These bundles are advertised by Mercurial repositories to facilitate
:ref:`bundle-based cloning <hgmo_bundleclone>`, which drastically reduces
the load on the hg.mozilla.org servers.

This service only runs on the master server.

pushdataaggregator.service
--------------------------

This systemd service monitors the state of the replication mirrors and
copies fully acknowledged/applied messages into a new Kafka topic
(``replicatedpushdata``).

The ``replicatedpushdata`` topic is watched by other services to react to
repository events. So if this service stops working, other services
will likely sit idle.

This service only runs on the master server.

``pulsenotifier.service``
-------------------------

This systemd service monitors the ``replicatedpushdata`` Kafka topic
and sends messages to Pulse to advertise repository events.

For more, see :ref:`hgmo_notification`.

The Pulse notifications this service sends are relied upon by various
applications at Mozilla. If it stops working, a lot of services don't
get notifications and things stop working.

This service only runs on the master server.

``snsnotifier.service``
-----------------------

This systemd service monitors the ``replicatedpushdata`` Kafka topic
and sends messages to Amazon S3 and SNS to advertise repository events.

For more, see :ref:`hgmo_notification`.

This service is essentially identical to ``pulsenotifier.service``
except it publishes to Amazon services, not Pulse.

``unifyrepo.service``
---------------------

This systemd service periodically aggregates the contents of various
repositories into other repositories.

This service and the repositories it writes to are currently experimental.

This service only runs on the master server.

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
for this, first look at systemd to see if all the consumer daemons
are running::

   $ systemctl status vcsreplicator@*.service

If any of the processes aren't in the ``active (running)`` state, the
consumer for that partition has crashed for some reason. Try to start it
back up::

   $ systemctl start vcsreplicator@*.service

You might want to take a look at the logs in the journal to make sure the
process is happy::

   $ journalctl -f --unit vcsreplicator@*.service

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

   $ /var/hg/venv_replication/bin/vcsreplicator-consumer /etc/mercurial/vcsreplicator.ini --skip --partition N

.. note::

   The ``--partition`` argument is semi-important: it says which Kafka partition
   to pull the to-be-skipped message from. The number should be the value
   from the systemd service that is failing / reporting lag.

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

check_pushdataaggregator_lag
----------------------------

``check_pushdataaggregator_lag`` monitors the lag of the aggregated replication
log (the ``pushdataaggregator.service`` systemd service).

The check verifies that the aggregator service has copied all fully
replicated messages to the unified, aggregate Kafka topic.

The check will alert if the number of outstanding ready-to-copy messages
exceeds configured thresholds.

.. important::

   If messages aren't being copied into the aggregated message log, derived
   services such as Pulse notification won't be writing data.

Expected Output
^^^^^^^^^^^^^^^

Normal output will say that all messages have been copied and all partitions
are in sync or within thresholds::

   OK - aggregator has copied all fully replicated messages

   OK - partition 0 is completely in sync (1/1)
   OK - partition 1 is completely in sync (1/1)
   OK - partition 2 is completely in sync (1/1)
   OK - partition 3 is completely in sync (1/1)
   OK - partition 4 is completely in sync (1/1)
   OK - partition 5 is completely in sync (1/1)
   OK - partition 6 is completely in sync (1/1)
   OK - partition 7 is completely in sync (1/1)

Failure Output
^^^^^^^^^^^^^^

The check will print a summary line indicating total number of messages
behind and a per-partition breakdown of where that lag is. e.g.::

   CRITICAL - 2 messages from 2 partitions behind

   CRITICAL - partition 0 is 1 messages behind (1/2)
   OK - partition 1 is completely in sync (1/1)
   CRITICAL - partition 2 is 1 messages behind (1/2)
   OK - partition 3 is completely in sync (1/1)
   OK - partition 4 is completely in sync (1/1)
   OK - partition 5 is completely in sync (1/1)
   OK - partition 6 is completely in sync (1/1)
   OK - partition 7 is completely in sync (1/1)

   See https://mozilla-version-control-tools.readthedocs.io/en/latest/hgmo/ops.html
   for details about this check.

Remediation to Check Failure
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

If the check is failing, first verify the Kafka cluster is operating as
expected. If it isn't, other alerts on the hg machines should be firing.
**Failures in this check can likely be ignored if the Kafka cluster is in
a known bad state.**

If there are no other alerts, there is a chance the daemon process has
become wedged. Try bouncing the daemon::

   $ systemctl restart pushdataaggregator.service

Then wait a few minutes to see if the lag decreased. You can also look at
the journal to see what the daemon is doing::

   $ journalctl -f --unit pushdataaggregator.service

If things are failing, escalate to VCS on call.

.. _hgmo_ops_check_pulsenotifier_lag:

check_pulsenotifier_lag
-----------------------

``check_pulsenotifier_lag`` monitors the lag of Pulse
:ref:`hgmo_notification` in reaction to server events.

The check is very similar to ``check_vcsreplicator_lag``. It monitors the
same class of thing under the hood: that a Kafka consumer has read and
acknowledged all available messages.

For this check, the consumer daemon is the ``pulsenotifier`` service running
on the master server. It is a systemd service (``pulsenotifier.service``). Its
logs are in ``/var/log/pulsenotifier.log``.

Expected Output
^^^^^^^^^^^^^^^

There is a single consumer and partition for the pulse notifier Kafka
consumer. So, expected output is something like the following::

   OK - 1/1 consumers completely in sync

   OK - partition 0 is completely in sync (159580/159580)

   See https://mozilla-version-control-tools.readthedocs.io/en/latest/hgmo/ops.html
   for details about this check.

Remediation to Check Failure
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

There are 3 main categories of check failure:

1. pulse.mozilla.org is down
2. The ``pulsenotifier`` daemon has crashed or wedged
3. The hg.mozilla.org Kafka cluster is down

Looking at the last few lines of ``/var/log/pulsenotifier.log`` should
indicate reasons for the check failure.

If Pulse is down, the check should be acked until Pulse service is restored.
The Pulse notification daemon should recover on its own.

If the ``pulsenotifier`` daemon has crashed, try restarting it::

   $ systemctl restart pulsenotifier.service

If the hg.mozilla.org Kafka cluster is down, lots of other alerts are
likely firing. You should alert VCS on call.

In some cases, ``pulsenotifier`` may repeatedly crash due to a malformed input
message, bad data, or some such. Essentially, the process encounters bad input,
crashes, restarts via systemd, encounters the same message again, crashes, and
the cycle repeats until systemd gives up. This scenario should be rare, which is
why the daemon doesn't ignore *bad* messages (ignoring messages could lead to
data loss).

If the daemon becomes wedged on a specific message, you can tell the daemon to
skip the next message by running::

   $ /var/hg/venv_tools/bin/vcsreplicator-pulse-notifier --skip /etc/mercurial/notifications.ini

This command will print a message like::

   skipped hg-repo-init-2 message in partition 0 for group pulsenotifier

Then exit. You can then restart the daemon (if necessary) via::

   $ systemctl start pulsenotifier.service

Repeat as many times as necessary to clear through the *bad* messages.

.. important::

   If you skip messages, please file a bug against
   ``Developer Services :: hg.mozilla.org`` and include the systemd journal
   output for ``pulsenotifier.service`` showing the error messages.

check_snsnotifier_lag
---------------------

``check_snsnotifier_lag`` monitors the lag of Amazon SNS
:ref:`hgmo_notification` in reaction to server events.

This check is essentially identical to ``check_pulsenotifier_lag`` except
it monitors the service that posts to Amazon SNS as opposed to Pulse.
Both services share common code. So if one service is having problems,
there's a good chance the other service is as well.

The consumer daemon being monitored by this check is tied to the
``snsnotifier.service`` systemd service. Its logs are in
``/var/log/snsnotifier.log``.

Expected Output
^^^^^^^^^^^^^^^

Output is essentially identical to :ref:`hgmo_ops_check_pulsenotifier_lag`.

Remediation to Check Failure
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Remediation is essentially identical to
:ref:`hgmo_ops_check_pulsenotifier_lag`.

The main differences are the names of the services impacted.

The systemd service is ``snsnotifier.service``. The daemon process is
``/var/hg/venv_tools/bin/vcsreplicator-sns-notifier``.

Adding/Removing Nodes from Zookeeper and Kafka
==============================================

When new servers are added or removed, the Zookeeper and Kafka clusters
may need to be *rebalanced*. This typically only happens when servers
are replaced.

The process is complicated and requires a number of manual steps. It
shouldn't be performed frequently enough to justify automating it.

Adding a new server to Zookeeper and Kafka
------------------------------------------

The first step is to assign a Zookeeper ID in Ansible. See
https://hg.mozilla.org/hgcustom/version-control-tools/rev/da8687458cd1
for an example commit. Find the next available integer **that hasn't been
used before**. This is typically ``N+1`` where ``N`` is the last entry
in that file.

.. note::

   Assigning a Zookeeper ID has the side-effect of enabling Zookeeper
   and Kafka on the server. On the next deploy, Zookeeper and Kafka
   will be installed.

Deploy this change via ``./deploy hgmo``.

During the deploy, some Nagios alerts may fire saying the Zookeeper
ensemble is missing followers. e.g.::

   hg is WARNING: ENSEMBLE WARNING - only have 4/5 expected followers

This is because as the deploy is performed, we're adding references to
the new Zookeeper server before it is actually started. These warnings
should be safe to ignore.

Once the deploy finishes, start Zookeeper on the new server::

   $ systemctl start zookeeper.service

Nagios alerts for the Zookeeper ensemble should clear after Zookeeper
has started on the new server.

Wait a minute or so then start Kafka on the new server::

   $ systemctl start kafka.service

At this point, Zookeeper and Kafka are both running and part of their
respective clusters. Everything is in a mostly stable state at this
point.

Rebalancing Kafka Data to the New Server
----------------------------------------

When the new Kafka node comes online, it will be part of the Kafka
cluster but it won't have any data. In other words, it won't
really be used (unless a cluster event such as creation of a new
topic causes data to be assigned to it).

To have the new server actually do something, we'll need to run
some Kafka tools to rebalance data.

The tool used to rebalance data is
``/opt/kafka/bin/kafka-reassign-partitions.sh``. It has 3 modes of operation,
all of which we'll use:

1. Generate a reassignment plan
2. Execute a reassignment plan
3. Verify reassignments have completed

All command invocations require a ``--zookeeper`` argument defining
the Zookeeper servers to connect to. The value for this argument should
be the ``zookeeper.connect`` variable from ``/etc/kafka/server.properties``.
e.g. ``hgssh4.dmz.scl3.mozilla.com:2181/hgmoreplication,hgweb11.dmz.scl3.mozilla.com:2181/hgmoreplication``.
**If this value doesn't match exactly, things may not go as planned.**

The first step is to generate a JSON document that will be used to perform
data reassignment. To do this, we need a list of broker IDs to move data
to and a JSON file listing the topics to move.

The list of broker IDs is the set of Zookeeper IDs as defined in
``ansible/group_vars/hgmo`` (this is the file you changed earlier to
add the new server). Simply select the servers you wish for data to
exist on. e.g. ``7,8,9,10,11``.

The JSON file denotes which Kafka topics should be moved. Typically
every known Kafka topic is moved. Use the following as a template::

   {
     "topics": [
       {"topic": "pushdata"},
       {"topic": "pushlog"},
       {"topic": "replicatedpushdata"},
       {"topic": "__consumer_offsets"}
     ],
     "version": 1
   }

Once you have all these pieces of data, you can run
``kafka-reassign-partitions.sh`` to generate a proposed reassignment plan::

   $ /opt/kafka/bin/kafka-reassign-partitions.sh \
     --zookeeper <hosts> \
     --generate \
     --broker-list <list> \
     --topics-to-move-json-file topics.json

This will output 2 JSON blocks::

   Current partition replica assignment

   {...}
   Proposed partition reassignment configuration

   {...}

You'll need to copy and paste the 2nd JSON block (the proposed reassignment)
to a new file, let's say ``reassignments.json``.

Then we can execute the data reassignment::

   $ /opt/kafka/bin/kafka-reassign-partitions.sh \
     --zookeeper <hosts> \
     --execute \
     --reassignment-json-file reassignments.json

Data reassignment can take up to several minutes. We can see the status
of the reassignment by running::

   $ /opt/kafka/bin/kafka-reassign-partitions.sh \
     --zookeeper <hosts> \
     --verify \
     --reassignment-json-file reassignments.json

If your intent was to move Kafka data off a server, you can verify data
has been removed by looking in the ``/var/lib/kafka/logs`` data on
that server. If there is no topic/partition data, there should be no
sub-directories in that directory. If there are sub-directories
(they have the form ``topic-<N>``), adjust your ``topics.json``
file, generate a new ``reassignments.json`` file and execute a
reassignment.

Removing an old Kafka Node
--------------------------

Once data has been removed from a Kafka node, it can safely be turned off.

The first step is to remove the server from the Zookeeper/Kafka list
in Ansible. See https://hg.mozilla.org/hgcustom/version-control-tools/rev/adc5024917c7
for an example commit. Deploy this via ``./deploy hgmo``.

Next, stop Kafka and Zookeeper from the server::

   $ systemctl stop kafka.service
   $ systemctl stop zookeeper.service

At this point, the old Kafka/Zookeeper node is shut down and should no
longer be referenced.

Clean up by disabling the systemd services::

   $ systemctl disable kafka.service
   $ systemctl disable zookeeper.service

Kafka Nuclear Option
--------------------

If Kafka and/or Zookeeper lose quorum or the state of the cluster gets
*out of sync*, it might be necessary to *reset* the cluster.

A hard *reset* of the cluster is the *nuclear option*: full data wipe and
starting the cluster from scratch.

A full reset consists of the following steps:

1. Stop all Kafka consumers and writers
2. Stop all Kafka and Zookeeper processes
3. Remove all Kafka and Zookeeper data
4. Define Zookeeper ID on each node
5. Start Zookeeper 1 node at a time
6. Start Kafka 1 node at a time
7. Start all Kafka consumers and writers

To stop all Kafka consumers and writers::

   # hgweb*
   $ systemctl stop vcsreplicator@*.service

   # hgssh*
   $ systemctl stop hg-master.target

You will also want to make all repositories read-only by creating the
``/etc/mercurial/readonlyreason`` file (and having the content say that
pushes are disabled for maintenance reasons).

To stop all Kafka and Zookeeper processes::

   $ systemctl stop kafka.service
   $ systemctl stop zookeeper.service

To remove all Kafka and Zookeeper data::

   $ rm -rf /var/lib/kafka /var/lib/zookeeper

To define the Zookeeper ID on each node (the ``/var/lib/zookeeper/myid`` file),
perform an Ansible deploy::

   $ ./deploy hgmo

.. note::

   The deploy may fail to create some Kafka topics. This is OK.

Then, start Zookeeper one node at a time::

   $ systemctl start zookeeper.service

Then, start Kafka one node at a time::

   $ systemctl start kafka.service

At this point, the Kafka cluster should be running. Perform an Ansible deploy
again to create necessary Kafka topics::

   $ ./deploy hgmo

At this point, the Kafka cluster should be fully capable of handling
hg.mo events. Nagios alerts related to Kafka and Zookeeper should clear.

You can now start consumer daemons::

   # hgweb
   $ systemctl start vcsreplicator@*.service

   # hgssh
   $ systemctl start hg-master.target

When starting the consumer daemons, look at the journal logs for any issues
connecting to Kafka.

As soon as the daemons start running, all Nagios alerts for the systems should
clear.

Finally, make repositories pushable again::

   $ rm /etc/mercurial/readonlyreason
