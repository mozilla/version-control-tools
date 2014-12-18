.. _server:

================================
Mozilla Server Operational Guide
================================

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
code. See :ref:`testing`.

The version-control-tools repository uses its own Mercurial version
separate from your system (or previously cloned) Mercurial. As such,
you'll have to specify it before the tests will run against the correct
version. Afterwards, you can run the test suite against your new version
of Mercurial.

.. code:: sh

   $ ./run-mercurial-tests.sh --with-hg=/path/to/system/hg

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
   hgweb1 $ yum clean metadata
   hgweb1 $ yum upgrade mercurial # (say Yes at the prompt or pass -y here)
   hgweb1 $ service httpd restart

Repeat this procedure until all webheads have been upgraded.

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
