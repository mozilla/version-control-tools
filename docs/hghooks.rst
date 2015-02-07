.. _hghooks:

===============
Mercurial Hooks
===============

The ``hghooks`` directory contains a number of Mercurial hooks used by
Mozilla projects.

The content of this directory originally derived from its own
repository. Changesets ``e11fee681380`` through ``1f927bcba52c`` contain
the import of this repository.

This directory has its origins in the operation of the Mercurial server
at Mozilla. It is an eventual goal to restructure the hooks to be usable
on both client and server.

Available Hooks
===============

changelog_correctness.py
------------------------

Older versions of Mercurial had a bug where the set of modified files stored in
the commit object were incomplete. Operations that relied on this cached set
of changed files (hooks, some revset queries, log) could have inaccurate
output if a buggy commit was present.

This hook looks for the presence of buggy metadata and rejects it.

commit-message.py
-----------------

This hook attempts to enforce that commit messages are well-formed. It is
targeted towards the Firefox commit message standard.

prevent_case_only_renames.py
----------------------------

This hook prevents file renames that only change the case of a file. e.g.
renaming ``foo`` to ``FOO`` would be disallowed.

This hooks exists to prevent issues with case-insensitive filesystems.

prevent_string_changes.py
-------------------------

This hook is used to prevent changes to strings in string frozen release
heads without the explicit approval from l10n-drivers.

prevent_uuid_changes.py
-----------------------

This hook prevents changes to IDL IIDs or UUIDs when they shouldn't be made.
This hook helps ensure binary compatibility of Firefox as it is released.

prevent_webidl_changes.py
-------------------------

This hook prevents changes to WebIDL files that shouldn't be made.

All WebIDL changes must be reviewed by a DOM peer and this hook enforces
that.

push_printurls.py
-----------------

This hook prints relevant information about a push that just completed.

It will print the URL of the changesets on https://hg.mozilla.org/. It
will also print TreeHerder URLs for Try pushes.

single_head_per_branch.py
-------------------------

This hook enforces that all Mercurial branches contain at most one head.

treeclosure.py
--------------

This hook prevents pushes to Firefox repositories that are currently closed.

trymandatory.py
---------------

This hook enforces the requirement that pushes to the Try repository contain
Try job selection syntax.

whitelist_releng.py
-------------------

This hook enforces a whitelist of accounts that are allowed to push to certain
Release Engineer repositories.
