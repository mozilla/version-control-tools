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
