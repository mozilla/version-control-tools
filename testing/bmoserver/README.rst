Bugzilla Server
===============

This directory contains code for running a Bugzilla server.

We want to run a Bugzilla server that is as close as possible to the
configuration of bugzilla.mozilla.org so that testing is accurate
and there won't be any surprises when we push to production.

Usage
=====

1. Install Vagrant
2. Run ``vagrant up``
3. Wait a while (there are lots of packages to download and install)

Basic image creation should take 10-15 minutes on a modern machine with
an SSD and a fast internet connection. A lot of that is installing Perl
packages from CPAN.

If you install the Bugzilla data dump (see below) expect image creation
to take ~40 minutes longer (50+ minutes on a modern machine).

Inside the VM, Bugzilla is available at http://localhost:80/. Outside of
the VM, Bugzilla is available at http://localhost:12000/.

The admin username and password is ``admin@example.com`` and
``password``.

Choice of Vagrant
=================

We use Vagrant + Puppet for creating and provisioning a virtual
machine running Bugzilla.

We would ideally use Docker. However, Docker is still quirky with
regards to containers that run multiple processes, thus requiring
an init process. After much toiling with Docker, it was decided that
it would be easier to use Vagrant for the time being.

The Puppet config is sufficiently standalone that it could be leveraged
by Docker as well.

MySQL Server Settings
=====================

Credentials are *root*/*root* and *bugs*/*bugs*. The Bugzilla database
is *bugs*.

The MySQL server is tuned for fast importing of the BMO data set.
Settings are adjusted to favor writes over reads. However, read
performance for basic analysis workloads should hopefully not be
impacted too much.

The server is also tuned for SSDs. If you are running on magnetic
storage, BMO data set import will take a long time.

bugzilla.mozilla.org Data
=========================

If you would like to import a dump of Mozilla's bugzilla.mozilla.org
data, grab a file from https://people.mozilla.org/~mhoye/bugzilla/
and save it into ``files/``. e.g.
``files/Mozilla-Bugzilla-Public-04-May-2014.sql.gz``.
During Puppet provision, the content from this file will be imported
into the database automatically.

Adding dump data later
----------------------

If you provision without a dump file and attempt to reprovision with
a dump file, this will likely result in error. To correct this,
drop the ``bugs`` database and reprovision::

   $ vagrant ssh
   $ mysql -uroot -proot -e 'DROP DATABASE bugs;'
   $ exit
   $ vagrant provision

Multiple dump files
-------------------

If there are multiple dump files in the ``files/`` directory, behavior
is undefined. Please only place 1 dump file in that directory!

Performance of dump importing
-----------------------------

MySQL has been tuned to make dump importing fast. In addition, we have
a wrapper script (``fastimport.py``) that adds some statements to the
import transaction to avoid excessive I/O.

If you have a modern machine, disk write I/O during import should be
40+ MB/s with read I/O almost non-existent (except during imports of
tables with FULLTEXT indexes).

Even with all the optimizations, it still takes ~40 minutes on modern
machines to import the dump. You have been warned.
