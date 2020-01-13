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

format-source
============

The extension provides a way to run code-formatting tools in a way that avoids
conflicts related to this formatting when merging/rebasing code across the
reformatting.

A new `format-source` command is provided, to apply a code formatting tool on
some specific files. This information is recorded into the repository and
reused when merging. The client doing the merge needs the extension for this
logic to kick in.

Code formatting tools have to be registered in the configuration. The tool
"name" will be used to identify a specific command accross all repositories.
It is mapped to a command line that must output the formatted content on its
standard output.

For each tool a list of files affecting the result of the formatting can be
configured with the "configpaths" suboption, which is read and registered at
"hg format-source" time.  Any change in those files should trigger
reformatting.

Example:
    [format-source]
    clang-format = [Path To Mozilla Repo]/mach clang-format --assume-filename $HG_FILENAME -p
    clang-format:configpaths = .clang-format, .clang-format-ignore
    clang-format:fileext = .cpp, .c, .h

We do not support specifying the mapping of tool name to tool command in the
repository itself for security reasons.

The code formatting information is tracked in a .hg-format-source file at the
root of the repository.

Warning: There is no special logic handling renames so moving files to a
directory not covered by the patterns used for the initial formatting will
likely fail.

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
