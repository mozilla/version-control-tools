.. _unified_repo:

=========================================
Working With a Unified Firefox Repository
=========================================

Traditionally, the various Firefox repositories (``mozilla-central``,
``mozilla-inbound``, ``mozilla-aurora``, etc) have been separate
repositories. They all share the same root commit
(``8ba995b74e18334ab3707f27e9eb8f4e37ba3d29``), so it is possible to combine
them locally. This has several benefits:

* You can easily switch between heads using ``hg up``
* You can easily compare changes across different heads using ``hg log``,
  ``hg diff``, and other tools.
* Landing a patch is as simple as ``hg rebase``.
* You only have to fetch the data associated with each commit exactly once
  (with separate repositories, you transfer down each commit *N* times).

Creating a Unified Repository
=============================

The recommended method to create a unified Firefox repository is documented as
part of the :ref:`firefoxtree extension documentation <firefoxtree>`.

Uplifting / Backporting Commits
===============================

Often times there are commits that you want to uplift to other projects
branches. e.g. a commit from ``mozilla-central`` should be uplifted to
``mozilla-aurora``. This operation is typically referred to as a
*backport* or a *cherry-pick*.

The ``hg graft`` command should be used to perform these kinds of
operations.

Say you wish to backport ``77bbac61cd5e`` from *central* to *aurora*.:

.. code:: sh

   # Ensure your destination repository is up to date.
   $ hg pull aurora
   ...

   # Update to the destination where commits should be applied.
   $ hg up aurora

   # Perform the backport.
   $ hg graft -r 77bbac61cd5e

When ``hg graft`` is executed, it will essentially *rebase* the
specified commits onto the target commit. If there are no merge
conflicts or other issues, it will commit the new changes automatically,
preserving the original commit message.

If you would like to edit the commit message on the new commit (e.g.
you want to add ``a=``), simply add ``--edit``::

   $ hg graft --edit -r 77bbac61cd5e

If Mercurial encounters merge conflicts during the operation, you'll
see something like the following:

.. code:: sh

   $ hg graft -r 77bbac61cd5e
   warning: conflicts during merge.
   merging foo incomplete! (edit conflicts, then use 'hg resolve --mark')
   abort: unresolved conflicts, can't continue
   (use hg resolve and hg graft --continue)

Read `Mercurial's conflict docs <http://mercurial.selenic.com/wiki/TutorialConflict>`_
for how to resolve conflicts. When you are done resolving conflicts,
simply run ``hg graft --continue`` to continue the graft where it left
off.

If you wish to backport multiple commits, you can specify a range of
commits to process them all at once:

.. code:: sh

   $ hg graft -r 77bbac61cd5e::e8f80db57b48

.. tip::

   ``hg graft`` is superior to other solutions like ``hg qimport``
   because ``hg graft`` will perform a 3-way merge and will use
   Mercurial's configured merge tool to resolve conflicts. This should
   give you the best possible merge conflict outcome.

Maintaining Multiple Checkouts With a Unified Repository
========================================================

Developers often maintain multiple checkouts / working directories of Firefox.
For example, you may do all your day-to-day work on ``mozilla-central`` but
also have a ``mozilla-beta`` checkout around for testing patches against
Firefox Beta.

A common reason why developers do this is because updating to different
commits frequently requires a build system clobber. This is almost always
true when updating between different Gecko versions.

Some people may say *I prefer maintaining separate clones because it means
I don't have to clobber as often.* What they are really saying is *I want to
maintain separate working directories that are independent.*

The solution to use is to use ``hg share``. ``hg share`` allows you to create
a new working copy of a repository that *shares* the backing repository store
with another.

Add the following to your Mercurial configuration file::

  [extensions]
  share =

Then, create a shared store as follows::

  $ hg share /path/to/existing/clone /path/to/new/checkout

Now, you can ``hg up`` inside both repositories independently! If you commit
to one, that commit will be available in the other checkouts using that
shared store.

.. tip::

   Mercurial 3.3 and newer support sharing bookmarks with repositories created
   with ``hg share``. To activate bookmark sharing, you'll need to add ``-B``
   to ``hg share``. e.g. ``hg share -B existing new-checkout``

.. caution::

   Users of MQ should exercise extreme caution when using shared stores.

   MQ operates at a low-level in Mercurial: every MQ operation is essentially
   creating or deleting commits from the store. Deleting commits from large
   repositories like Firefox's can be a very expensive operation. You not
   only pay a penalty at operation time, but all the shared repositories may
   have expensive computations to perform the next time the repository is
   accessed.

   MQ users are advised to not use ``hg share``.

   MQ users are advised to switch to head/bookmark-based development to avoid
   these limitations.
