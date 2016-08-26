.. _hgmo_upgrading:

===================
Upgrading Mercurial
===================

This document describes how to upgrade the Mercurial version deployed
to hg.mozilla.org.

Managing Mercurial Packages
===========================

We generally don't use Mercurial packages provided by upstream or from
distros because they aren't suitable or aren't new enough. So, we
often need to build them ourselves.

Building RPMs
-------------

Mercurial RPMs are created by invoking ``make`` targets in Mercurial's
build system. From a Mercurial source checkout::

   $ make -j2 docker-centos6 docker-centos7

This will build Mercurial RPMs in isolated Docker containers and store
the results in the ``packages/`` directory. ``.rpm`` files can be found
under ``packages/<distro>/RPMS/*.rpm``. e.g.
``packages/centos7/RPMS/x86_64/mercurial-3.9-1.x86_64.rpm``.

.. note::

   CentOS 6 RPMs are configured to use Python 2.6, as that is the Python
   used by CentOS 6 by default. Various Mercurial extensions at Mozilla
   require Python 2.7. So the *system* Mercurial RPMs produced via this
   method aren't guaranteed to work with everything. Furthermore, Python
   2.7 is faster than Python 2.6. For these reasons, it is recommended
   to avoid running Mercurial from the system Python on CentOS 6. Instead,
   run CentOS 7 or install Python 2.7 and run Mercurial from a virtualenv.

Building .deb Packages
----------------------

The process for producing Debian .deb packages is similar: run Mercurial's
make targets for building packages inside Docker::

   $ make docker-ubuntu-xenial

``.deb`` files will be available in the ``packages/`` directory.

Uploading Files to S3
---------------------

Built packages are uploaded to the ``moz-packages`` S3 bucket.

CentOS 6 packages go in the ``CentOS6`` folder. CentOS 7 packages in the
``CentOS7`` folder.

When uploading files, they should be marked as world readable, since we
have random systems downloading from this bucket.
