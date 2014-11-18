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
