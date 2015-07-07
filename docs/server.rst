.. _server:

================================
Mozilla Server Operational Guide
================================

hg.mozilla.org Hooks, Extensions, and Customizations Upgrade
============================================================

All code running on the servers behind hg.mozilla.org is in the
version-control-tools repository (or at least it should be - there are
still some components coming from sysadmins Puppet).

Deployment of new code to hg.mozilla.org is performed via an Ansible
playbook defined in the version-control-tools repository. To deploy new
code, simply run::

   $ ./deploy hgmo

.. important::

   Files from your local machine's version-control-tools working copy
   will be installed on servers. Be aware of any local changes you have
   performed, as they might be reflected on the server.

Mercurial Software Upgrade Instructions
=======================================

Targetted machines
------------------

These instructions should enable anybody with the correct access and
authorization to safely deploy a new version of Mercurial into
production on:

*  hgwebXX.dmz.scl3.mozilla.com
*  hgsshX.dmz.scl3.mozilla.com
*  hgssh.stage.dmz.scl3.mozilla.com

Overview
--------

This process has a few steps. You'll need to:

*  Read Mercurial's commit/change log to determine if there are any
   concerning changes (optional)
*  Set up a version-control-tools testing environment
*  Run tests against the new version in the version-control-tools
   testing environment
*  Upload the system package to mrepo (Mozilla's internal RHEL yum
   repository)
*  Coordinate with build-sheriffs (and other releng folk) for an
   appropriate time to do the upgrade
*  Remove hosts from the Zeus load balancer
*  Upgrade each host individually
*  Re-add and confirm correctness

Doing pre-upgrade tests
-----------------------

In this section we'll make sure that the Mercurial version upgrade isn't
going to inadvertantly break things.

You should start by having a checked out copy of mercurial-repo on your
system. Once you have it, you'll want to ``hg pull`` to obtain the latest
code, find the correct tag with ``hg tags``, then check it out with ``hg
checkout``. You'll also want to read the logs between versions.

.. code:: sh

   $ hg clone http://selenic.com/hg mercurial-repo
   $ cd mercurial-repo
   $ hg checkout 3.2.2
   $ hg log -r 3.2.1:3.2.2
   ...

Afterwards you'll want to run all the automated checks against this new
code. See :ref:`devguide_testing`.

The version-control-tools repository uses its own Mercurial version
separate from your system (or previously cloned) Mercurial. As such,
you'll have to specify it before the tests will run against the correct
version. Afterwards, you can run the test suite against your new version
of Mercurial.

.. code:: sh

   $ ./run-tests --with-hg=/path/to/system/hg

Assuming all tests pass you can do a little dance, then move on to the
next step.

Deploying the Mercurial Package
-------------------------------

This information was basically copied from Mana:
https://mana.mozilla.org/wiki/display/SYSADMIN/Building+and+Deploying+Mercurial+packages

RPMs for Mercurial are built as part of continuous integration. You
should be able to find some RPMs at
https://ci.mozilla.org/job/version-control-tools/.

.. code:: sh

     ssh $ wget https://ci.mozilla.org/job/version-control-tools/lastSuccessfulBuild/artifact/rpms/<version>.rpm
     ssh $ scp mercurial-${HG_VERSION}*.rpm mrepo1.dmz.scl3.mozilla.com:
     ssh $ ssh -A mrepo1.dmz.scl3.mozilla.com
     mrepo1 $ sudo mv mercurial-${HG_VERSION}*.rpm /data/mrepo-src/6Server-x86_64/mozilla
     mrepo1 $ sudo update-mrepo mozilla # This part takes a few minutes
     mrepo1 $ exit

The package should now be built and live on Mozilla's yum repository.
Now all that's left to do is coordinate the upgrade with other folks and
do the actual upgrade.

Coordinating the upgrade
------------------------

Please get in touch with the sheriffs and person on build-duty about the
work that you're doing. Tell them that you're upgrading Mercurial on the
hg.mozilla.org servers and that you're following the instructions
located here.

You can find the on-duty Sheriff in ``#releng`` (they will have
``|Sheriffduty`` appended to their name). You'll want to ping that person
and anybody who has ``|buildduty`` next to their name as well. These will
be the people who are the likeliest to tell you if something goes wrong
with the upgrade. You'll also likely want to send an email to
``sheriffs@mozilla.org`` explaining the work, so those thare are on duty
next will be able to tell you if they find something funny later.

If extra caution is warranted, a bug should be filed against the Change Advisory
Board. This board will help you schedule the upgrade work. Details can be found
at https://wiki.mozilla.org/IT/ChangeControl.

Performing the upgrade
----------------------

Webheads
^^^^^^^^

The next part will involve taking the hosts out of load balancer
rotation an, upgrading their software, then adding them back in. Zeus is
our internal load balancer, and each host has an entry in a *pool*. You
can access the Zeus load balancer web interface at
https://zlb1.ops.scl3.mozilla.com:9090. This is an IT-controlled host
and thus the password is in the sysadmins gpg-encrypted keyring.

Using the Zeus web interface, you'll want to find the ``hgweb-http`` pool
and open its pool page. After this, you'll change the first host's
status to ``draining``, then click ``Update``. After the page reloads you'll
see a little faucet next to the host. This means that the host is
draining. If you hover your mouse over the faucet icon you'll see a
tooltip saying ``X Connections``. When X reaches 0, no remaining HTTP
connections exist to the host. This means it is safe to SSH into the
host and perform the upgrade.

.. code:: sh

   $ ssh ssh.mozilla.com -A
   ssh $ ssh hgweb1.dmz.scl3.mozilla.com
   hgweb1 $ yum-wrapper clean metadata
   hgweb1 $ yum-wrapper upgrade mercurial # (say Yes at the prompt or pass -y here)
   hgweb1 $ service httpd restart

Repeat this procedure until all webheads have been upgraded.

Re-add and confirm correctness
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

After the host has been upgraded, it should be tested to ensure that the host is
still serving correctly. There is no formal process to do this, as the testing
is done previously through the v-c-t testing framework. Still, a good test is to
run elinks against the localhost to ensure that the front page and a single
repository will load.

.. code:: sh

   $ elinks -dump http://localhost/
   ...
   $ elinks -dump http://localhost/mozilla-central

If you have cause for concern, the httpd's logs should be checked. These are
located in /var/log/httpd/hg.mozilla.org/.

If everything looks good, then re-add the host back to the node pool in Zeus.

SSH Master hosts
^^^^^^^^^^^^^^^^

These hosts are also in Zeus, but belong to two different pools. The
active one (typically pointing at ``hgssh1.dmz.scl3.mozilla.com``) and the
``failover`` pool for when the active pool is not available (or
intentionally disabled).

First, start by upgading the failover host in a manner similar to the
procedure described for the webheads (sans restarting httpd). Next,
you'll need to wait until there is a period of no hg activity (described
below), then ``Disable`` the host in Zeus. This will cause the failover
pool to activate, directing traffic to ``hgssh2`` while you upgrade hgssh1.
Repeat the upgrade procedure for hgssh1.

Finding a period of inactivity on hgssh
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

There's no automated way of waiting for a period of inactivity here.
You'll simply need to SSH into the running host (``hg.mozilla.org``) and run

.. code:: sh

   $ ps aux|grep hg

Looking for currently running processes. If you can't find any, then
it's safe to perform the Zeus SSH pool failover. If there are existing
jobs running, plesae wait for them to finish.

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
