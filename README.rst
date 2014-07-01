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

bzexport
--------

The bzexport extension provides commands for interacting with Bugzilla.
It's known for its namesake ``hg bzexport`` command, which exports/uploads
patches to Bugzilla. It also offers an ``hg newbug`` command to create
new bugs from the command line.

This extension lives under ``hgext/bzexport``.

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

Testing
=======

Testing requires a special Python environment. To create this
environment:

  $ ./create-test-environment
  $ source venv/bin/activate

Then, launch the tests:

  $ ./run-mercurial-tests.py
