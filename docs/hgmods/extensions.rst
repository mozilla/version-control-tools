.. _hgmods_extensions:

==========
Extensions
==========

This repository contains a number of Mercurial extensions. Each is
described in the sections below.

All extensions are located under the ``hgext/`` subdirectory.

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

serverlog
=========

The serverlog extension hacks up some Mercurial internals to record
forensics that are useful for Mercurial server operators.
