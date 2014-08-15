=============================
Mozilla Version Control Tools
=============================

This repository contains tools, extensions, hooks, etc to support version
control at Mozilla.

The canonical repository is https://hg.mozilla.org/hgcustom/version-control-tools/

Mercurial Extensions
====================

This repository contains a number of Mercurial extensions. Each is
described in the sections below.

All extensions are located under the ``hgext/`` subdirectory.

bundleclone
-----------

The bundleclone extension is an experiment extension that allows
Mercurial servers to advertise where pre-generated bundles may be
fetched from. When ``hg clone`` is performed, the client will fetch a
static bundle file then do an incremental ``hg pull``. This is much more
efficient for the server.

bzexport
--------

The bzexport extension provides commands for interacting with Bugzilla.
It's known for its namesake ``hg bzexport`` command, which exports/uploads
patches to Bugzilla. It also offers an ``hg newbug`` command to create
new bugs from the command line.

This extension lives under ``hgext/bzexport``.

bzpost
------

The bzpost extension will automatically update Bugzilla after pushing
changesets that reference bugs.

firefoxtree
-----------

The firefoxtree extension makes working with the various Firefox
repositories much more pleasant.

mozext
------

*mozext* is a Swiss Army Knife for Firefox development. It provides a
number of features:

* It defines aliases for known Firefox repositories. You can do
  ``hg pull central``, etc.
* It provides a mechanism for tracking each repository via bookmarks,
  allowing you to more easily operate a unified repository.
* Changes to Python files are automatically checked for style.
* Pushlog data is synchronized to a local database.
* Bug data is extracted from commit messages and stored in a database.
* Many revision set and template functions are added.

If you are looking to turn Mercurial into a more powerful query tool or
want to maintain a unified repository, *mozext* is very valuable.

This extension lives under ``hgext/mozext``.

pushlog-legacy
--------------

This is a collection of code that modifies Mercurial to support
recording when and who pushes to repositories.

qbackout
--------

The qbackout extension provides assitance to help perform code backouts
the Mozilla way.

qimportbz
---------

The qimportbz extension allows you to easily import patches from
Bugzilla.

reviewboard
-----------

The reviewboard extension provides a Mozilla-centric workflow for
performing code review with ReviewBoard and Bugzilla.

serverlog
---------

The serverlog extension hacks up some Mercurial internals to record
forensics that are useful for Mercurial server operators.

Hooks
=====

The hghooks directory contains various Mercurial hooks. The content of
this directory originally derived from its own repository. Changesets
e11fee681380 through 1f927bcba52c contain the import of this repository.

Testing
=======

This repository contains extensive tests of the functionality therein.
To run the tests, you'll need a Linux or OS X install. You can always
obtain a Linux install by running a virtual machine.

Testing requires a special Python environment. To create this
environment:

  $ ./create-test-environment
  $ source venv/bin/activate

Then, launch the tests:

  $ ./run-mercurial-tests.py

To see help on options that control execution:

  $ ./run-mercurial-tests.py --help

Unknown script arguments will be proxied to Mercurial's ``run-tests.py``
testing harness.

Common tasks are described in the sections below.

Run all tests, 8 at a time
--------------------------

  $ ./run-mercurial-tests -j8

Obtain code coverage results (makes tests run slower)
-----------------------------------------------------

  $ ./run-mercurial-tests --cover

Test a single file
------------------

  $ ./run-mercurial-tests path/to/test.t

Run a test in debug mode
------------------------

  $ ./run-mercurial-tests -d path/to/test.t

Run tests against all supported Mercurial versions
--------------------------------------------------

  $ ./run-mercurial-tests --all-versions

Run tests with a specific Mercurial installation
------------------------------------------------

  $ ./run-mercurial-tests --with-hg=/path/to/hg
