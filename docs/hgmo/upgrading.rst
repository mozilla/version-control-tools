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

Upgrading And Modifying Templates
=================================

The repository contains a vendored copy of Mercurial's templates plus
modifications in the ``hgtemplates/`` directory. These templates are
used by the hgweb server.

We have made several modifications to the templates. The most significant
modification is the addition of the *gitweb_mozilla* theme, which is a
fork of the *gitweb* theme. We have also made a number of changes to
the *json* theme to facilitate rendering additional data not exposed
by Mercurial itself.

Modifying Templates
-------------------

When modifying a template, it isn't enough to simply change a template
file in ``hgtemplates/``: you must also track that change by recording
it somewhere in ``hgtemplates/.patches/``.

Most modifications are tracked by patch files. Essentially, there exists
a standalone patch file describing the change. To modify a template via
patch file, do the following:

1. Create a new Mercurial changeset like you normally would. i.e. make file
   changes and ``hg commit`` the result.
2. Export the just-created changeset to a standalone patch file. e.g.
   ``hg export . > hgtemplates/.patches/my-change.patch``.
3. Track the new patch file via ``hg add hgtemplates/.patches/<name>.patch``.
4. Modify the ``hgtemplates/.patches/series`` file and add the new
   patch file to the list.
5. Run ``run-tests /hgserver/tests/test-template-sync.t`` and verify the test
   passes.

``test-template-sync.t`` verifies that the current state of the checkout
matches what would be obtained if all modifications were performed on a fresh
copy of the templates. In other words, it verifies we can reproduce the
current state of the templates.

If the test passes, ``hg commit --amend`` or ``hg histedit`` your
changesets so the modifications to ``hgtemplates/.patches`` are part of
the changeset that modifies files in ``hgtemplates/``. Then submit that
for review and land when acceptable.

For other modifications (such as adding or removing a file), see the
file lists at the top of ``hgtemplates/.patches/mozify-templates.py``
to influence behavior.

Upgrading Templates
-------------------

When Mercurial is upgraded, we need to synchronize our vendored templates
with the new templates from upstream.

To do that, we run the ``hgtemplates/.patches/mozify-templates.py`` script.
This script will:

1. Wipe away ``hgtemplates/``.
2. Copy the canonical templates from upstream into ``hgtemplates/``.
3. Perform special modifications to templates (notably adding and removing
   certain files and performing hard-coded template transforms).
4. Attempt to apply and commit each patch listed in
   ``hgtemplates/.patches/series``.

.. important::

   Ensure your working directory is clean and ``hgtemplates/`` is free of
   untracked files before continuing. Run ``hg revert -C hgtemplates/``
   and ``hg purge hgtemplates/`` to do this.

To perform an upgrade::

   $ hgtemplates/.patches/mozify-templates.py /path/to/mercurial/templates \
       hgtemplates hgtemplates

e.g.::

   $ hgtemplates/.patches/mozify-templates.py venv/mercurials/4.6.2/lib/python2.7/site-packages/mercurial/templates \
       hgtemplates hgtemplates

This tells the script to copy templates from the 1st argument, to grab
patches and files from the 2nd argument, and to write the result into the
3rd argument.

If everything is successful, several commits would have been made. You can
use e.g. ``hg show stack`` (assuming the ``show`` extension is enabled) to
see them. These changesets can be removed via ``hg prune`` or ``hg strip``
without causing harm.

If the script fails, chances are it failed to run ``hg import`` to apply
a patch. Your working directory may or may not be in a good state. Check
that with ``hg status`` and resolve via ``hg revert`` etc as appropriate.

To recover from a non-working patch file, you'll need to update the
failed patch file until it applies cleanly. To do that, look at the
process output for the name of the patch file that failed to apply. Next,
you'll attempt to apply it manually. e.g. if the ``foo.patch`` file fails::

   $ hg import --partial hgtemplates/.patch/foo.patch

You will then need to resolve any conflicts, fix the files until they are
in the state you want, etc. Then ``hg commit --amend`` the result. This
will produce a new changeset with a working version of the patch.

Next, you will update the failing ``.patch`` file with the new version and
commit the result. e.g.

   $ hg export > hgtemplates/.patch/foo.patch
   $ hg commit -m 'hgtemplates: update foo.patch for Mercurial 4.7 upgrade'

Then you need to start the template upgrade process over from the beginning
with the modified ``.patch`` file in place. e.g.::

   $ hg up @
   $ hg rebase -s tip -d .
   $ hgtemplates/.patches/mozify-templates.py venv/mercurials/4.6.2/lib/python2.7/site-packages/mercurial/templates \
       hgtemplates hgtemplates

You can also safely ``hg prune`` or ``hg strip`` the changesets produced by
``mozify-templates.py``.

Once you've repeated this process and ``mozify-templates.py`` completes
without error, ``hgtemplates/`` now contains the upstream templates plus
our modifications.

Then, modify ``hgserver/tests/test-template-sync.t`` so it picks up
the Mercurial templates from the appropriate Mercurial version in its
``mozify-templates.py`` invocation. And run this test and verify all is
happy. Then commit that change.

At this point, the repository has several commits. There could be
modifications to ``hgtemplates/.patches/``. There will be changesets
tracking the upstream changes to ``hgtemplates/`` and changes made by
each patch. And there should be a changeset for the change to
``test-template-sync.t``.

At this point, it is recommended to run ``hg histedit`` and roll all the
changesets together. This will produce a unified changeset containing every
change. It should effectively be a diff of the upstream changes plus whatever
changes to patches were needed to accommodate upstream changes. This
changeset should be suitable for review.
