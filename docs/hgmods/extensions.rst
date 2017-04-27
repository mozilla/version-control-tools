.. _hgmods_extensions:

==========
Extensions
==========

This repository contains a number of Mercurial extensions. Each is
described in the sections below.

All extensions are located under the ``hgext/`` subdirectory.

bzexport
========

The bzexport extension provides commands for interacting with Bugzilla.
It's known for its namesake ``hg bzexport`` command, which exports/uploads
patches to Bugzilla. It also offers an ``hg newbug`` command to create
new bugs from the command line.

This extension lives under ``hgext/bzexport``.

bzpost
======

The bzpost extension will automatically update Bugzilla with comments
containing the URL to pushed changesets after pushing changesets that
reference bugs. The implementation is highly tailored towards the
Firefox workflow.

firefoxtree
===========

The firefoxtree extension makes working with the various Firefox
repositories much more pleasant.

For more, read :ref:`it's documentation <firefoxtree>`.

mozext
======

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
==============

This is a collection of code that modifies Mercurial to support
recording when and who pushes to repositories.

qbackout
========

The qbackout extension provides assitance to help perform code backouts
the Mozilla way.

qimportbz
=========

The qimportbz extension allows you to easily import patches from
Bugzilla.

reviewboard
===========

The reviewboard extension provides a Mozilla-centric workflow for
performing code review with ReviewBoard and Bugzilla.

This extension is a component of :ref:`MozReview <mozreview>`, Mozilla's
code review service.

serverlog
=========

The serverlog extension hacks up some Mercurial internals to record
forensics that are useful for Mercurial server operators.
