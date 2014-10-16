=============================
Mozilla Version Control Tools
=============================

This repository contains tools, extensions, hooks, etc to support version
control at Mozilla.

This repository contains the code that Mozilla uses in production to
power ``hg.mozilla.org``.

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
