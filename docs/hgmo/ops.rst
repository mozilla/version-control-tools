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
