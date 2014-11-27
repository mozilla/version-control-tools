.. _firefoxtree:

=====================
firefoxtree Extension
=====================

The ``firefoxtree`` Mercurial extension enhances the interaction with
Firefox repositories.

Background on Multiple Repositories
===================================

Firefox developers typically interact with multiple repositories. There
is the canonical head of Firefox development,
`mozilla-central <https://hg.mozilla.org/mozilla-central>`_. There are
landing repositories such as
`mozilla-inbound <https://hg.mozilla.org/integration/mozilla-inbound>`_
and
`fx-team <https://hg.mozilla.org/integration/fx-team>`_.
Then there are release repositories like
`mozilla-aurora <https://hg.mozilla.org/releases/mozilla-aurora>`_,
`mozilla-beta <https://hg.mozilla.org/releases/mozilla-beta>`_, and
`mozilla-release <https://hg.mozilla.org/releases/mozilla-release>`_.

**All of these repositories share the same initial commit and thus are
one logical repository.** However, for historical and continuity
reasons, the separate topological heads of this conceptual single
repository are all stored in separate repositories on Mozilla's
servers.

Consolidating the Repositories Locally
======================================

Traditionally, Mozilla developers maintain separate clones of each
repository. There is thus a one to one mapping between local and remote
repositories. For example, you may have separate ``mozilla-central`` and
``mozilla-inbound`` directories/clones to track the different *upstream*
repositories. This practice is grossly inefficient. The shared repository
data is fetched and stored multiple times. This creates more load for
the server, occupies more space on disk, and adds overhead to common
tasks such as rebasing from central to inbound.

The *firefoxtree* extension allows you to easily combine the separate
remote repositories into a local, single, unified repository.

When you ``hg pull`` from a known Firefox repository, *firefoxtree* will
automatically create a local-only *label* corresponding to the name of the
remote repository. These labels will manifest as tags. For example::

  $ hg pull https://hg.mozilla.org/mozilla-central
  pulling from https://hg.mozilla.org/mozilla-central
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  added 130 changesets with 651 changes to 329 files
  (run 'hg update' to get a working copy)

  $ hg log -r tip
  changeset:   248552:d380166816dd
  tag:         central
  tag:         tip
  user:        ffxbld
  date:        Sat Nov 08 03:20:23 2014 -0800
  summary:     No bug, Automated blocklist update from host bld-linux64-spot-144 - a=blocklist-update

You can see from the output of ``hg log`` that changeset
``d380166816dd`` has the ``central`` *tag* associated with it.

The following example demonstrates how to pull various Firefox
repositories into a single local repository and then how to navigate
between commits.::

  $ hg pull https://hg.mozilla.org/integration/mozilla-inbound
  pulling from https://hg.mozilla.org/integration/mozilla-inbound
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  added 34 changesets with 140 changes to 113 files (+1 heads)
  (run 'hg heads .' to see heads, 'hg merge' to merge)

  $ hg pull https://hg.mozilla.org/integration/b2g-inbound
  pulling from https://hg.mozilla.org/integration/b2g-inbound
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  added 21 changesets with 119 changes to 13 files (+1 heads)
  (run 'hg heads .' to see heads, 'hg merge' to merge)

  $ hg up central
  327 files updated, 0 files merged, 10 files removed, 0 files unresolved

  $ hg log -r .
  changeset:   248552:d380166816dd
  tag:         central
  tag:         tip
  user:        ffxbld
  date:        Sat Nov 08 03:20:23 2014 -0800
  summary:     No bug, Automated blocklist update from host bld-linux64-spot-144 - a=blocklist-update

  $ hg up inbound
  118 files updated, 0 files merged, 2 files removed, 0 files unresolved

  $ hg log -r .
  changeset:   248586:e021487d1297
  tag:         inbound
  user:        Connor <cojojennings@gmail.com>
  date:        Wed Oct 29 23:58:03 2014 -0400
  summary:     Bug 575094 - Modify how prefservice is accessed so that it's from the parent process and not from the child process. Also re-enable test_bug528292_wrap.js. r=jdm

.. tip::

   If you are familiar with Git, it may help to think of these
   repository labels as *remote refs*.

To view a summary of which repositories are on which changesets, run
``hg fxheads``::

  $ hg fxheads
  248607:a7a2bacecce7 b2ginbound tip Bumping manifests a=b2g-bump
  248552:d380166816dd central No bug, Automated blocklist update from host bld-linux64-spot-144 - a=blocklist-update
  246125:c742dcb56135 fx-team Bug 1088729 - Only allow http(s) directory links and https/data images [r=adw]
  248586:e021487d1297 inbound Bug 575094 - Modify how prefservice is accessed so that it's from the parent process and not from the child process. Also re-enable test_bug528292_wrap.js. r=jdm

.. tip::

   The output of ``hg fxheads`` is only current from the last time you
   pulled from each repository. Given the frequency of pushes to the
   Firefox repositories, at least one of your labels will likely be out
   of date.

Pre-defined Repository Paths
============================

Typically, if you are pulling from multiple remotes, you need to define
the names and URLs of those remotes in the ``[paths]`` section of the
repository's ``.hg/hgrc`` file. The names and URLs of Firefox
repositories are well-known, so *firefoxtree* does this for you.

Simply type ``hg pull <tree>`` to pull from a known Firefox repository.
For example::

  $ hg pull central
  $ hg pull inbound

Or type ``hg push <tree>`` to push to a Firefox repository.::

  $ hg push inbound
  $ hg push aurora

.. tip::

   The registered name aliases should be intuitive. Try a name of a
   popular Firefox repository. It should *just work*. If you get stumped
   or want to see the full list of names, read
   `the source <https://hg.mozilla.org/hgcustom/version-control-tools/file/default/pylib/mozautomation/mozautomation/repository.py>`_.

Safer Push Defaults
===================

The default behavior of ``hg push`` is to want to transfer all
non-remote changesets to the remote. In other words, if you have pulled
mozilla-central and mozilla-aurora into the same repository and you
``hg push ssh://hg.mozilla.org/mozilla-central``, Mercurial will want to
transfer all of mozilla-aurora's changesets to central!

The way you are supposed to do this is to always pass a ``--rev`` or
``-r`` argument to ``hg push`` to tell Mercurial exactly what changesets
to push. Commonly, you want to push the working copy's commit, so the
command to use would be ``hg push -r . <remote>``.

Since ``hg push -r .`` is almost always what is wanted when pushing to
a Firefox repository, *firefoxtree* automatically changes ``hg push``
to behave like ``hg push -r .`` when pushing to a Firefox repository.

Working with Unified Repositories and Repository Labels
=======================================================

Astute readers may have noticed that Mercurial is reporting the
repository labels as *tags*. However, they don't behave like *tags*.
The ``.hgtags`` file is not updated and ``hg push`` won't transfer them.
Under the hood, the extension is using an extension-only feature of
Mercurial to supplement the tags list. The labels are being reported as
tags, but have almost nothing to do with actual tags.

The repository labels can only be modified by *firefoxtree*.
Furthermore, they are only modified when running ``hg pull``. Unlike
bookmarks or branches, user actions such as committing will **not
advance the labels**.
