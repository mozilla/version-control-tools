.. _hgmods_hooks:

=====
Hooks
=====

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

Hook Development Standards
==========================

Hooks are written and loaded into Mercurial as Python modules. This goes
against recommendations by the Mercurial project. However, we do this for
performance reasons, as spawning new processes for hooks wastes valuable
wall time during push. (Mercurial recommends against in-process hooks
because they don't make promises about the stability of the internal API.)

Hooks should be unit tested via ``.t tests`` and should strive for 100%
code coverage. We don't want any surprises in production. We don't want
to have to manually test hooks when upgrading Mercurial. We should have
confidence in our automated tests.

Pre-commit (notably ``pretxnchangegroup``) hooks should filter the ``strip``
source and always return success for these. If an ``hg strip`` operation
is running, the changesets already got into the repository, so a hook
has no business checking them again.

Any hook change touching a Mercurial API should be reviewed by someone who
knows Mercurial internals. You should default to getting review from
``gps``.

Hooks connecting to external systems or performing process that could be
deferred will be heavily scrutinized. We want ``hg push`` operations to
be fast. Slow services, networks, or CPU or I/O intensive hooks all
undermine that goal.
