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

Unified Repository on hg.mozilla.org
====================================

``https://hg.mozilla.org/mozilla-unified`` is a *read-only* unified
repository containing all of the commits on the ``default`` branch of
the various Firefox repositories (mozilla-central, inbound, aurora,
beta, release, esr, etc) in chronological order by push time.

Advantages of the Unified Repo
------------------------------

If you pull from multiple Firefox repositories or maintain multiple
clones, pulling from the unified repository will be faster and
require less local storage than pulling from or cloning *N* repositories.

The unified repository **does not include extra branches**, notably the
``*_RELBRANCH`` branches. If you've ever pulled the mozilla-beta
or mozilla-release repositories, you know how annoying the presence
of these branches can be.

The unified repository features **bookmarks that track each canonical
repository's head**. For example, the ``central`` bookmark tracks the
current head of mozilla-central. If you naively pulled all the Firefox
repositories into a local Mercurial repository, you would have multiple
*anonymous* heads on the ``default`` branch and you wouldn't know which
head belonged to which Firefox repository. The bookmarks solve this
problem.

In a nutshell, the unified repository solves many of the problems
with Firefox's multi repository management model in a way that doesn't
require client-side workarounds like the
:ref:`firefoxtree extension <firefoxtree>`.

Working with the Unified Repo (Vanilla Mercurial)
-------------------------------------------------

Here is the basic workflow for interacting with the unified
repo when using a vanilla Mercurial configuration (no ``firefoxtree``
extension).

First, clone the repo::

   $ hg clone --uncompressed https://hg.mozilla.org/mozilla-unified

Update to a bookmark you want to base work off of::

   $ hg up central
   42 files updated, 0 files merged, 0 files removed, 0 files unresolved
   (activating bookmark central)

Then start a new bookmark to track your work::

   $ hg bookmark myfeature

Then make changes and commit::

   <edit some files>
   $ hg commit

If you want to rebase::

   $ hg pull
   $ hg rebase -b myfeature -d central

Be sure you've activated your own bookmark or deactivated the Firefox bookmark
before committing or you may move the bookmark from the server. The easiest
way to do this is::

   $ hg up .
   (leaving bookmark central)

.. tip::

   Facebook's `scm-prompt.sh <https://bitbucket.org/facebook/hg-experimental/src/default/scripts/scm-prompt.sh?at=default&fileviewer=file-view-default>`_
   implements shell prompt integration for both Mercurial and Git. It displays
   the currently active bookmark, which is useful to prevent accidentally
   committing on bookmark belonging to a Firefox repo.

Working with the Unified Repo (firefoxtree)
-------------------------------------------

If you have the ``firefoxtree`` extension installed, the behavior of
the unified repository changes slightly. Instead of pulling bookmarks,
the ``firefoxtree`` extension stores labels of the same name in a read-only
namespace instead.

Not using bookmarks means you can't accidentally update your local bookmarks
corresponding to Firefox repo state and drift out of sync with reality. It
also means you don't have to activate and deactivate bookmarks locally: enabling
you to engage in simpler workflows.

Here is how workflows typically look like with ``firefoxtree`` installed.

First, clone the repo::

   $ hg clone --uncompressed https://hg.mozilla.org/mozilla-unified

Update to the repo/head you want to work on::

   $ hg up central
   42 files updated, 0 files merged, 0 files removed, 0 files unresolved
   (activating bookmark central)

**Optionally** create a new bookmark to track your work::

   $ hg bookmark myfeature

Then make changes and commit::

   <edit some files>
   $ hg commit

If you want to rebase::

   $ hg pull
   $ hg rebase -b myfeature -d central

The ``firefoxtree`` extension will also print the number of new commits
to each repo since last pull.::

   $ hg pull
   pulling from https://hg.mozilla.org/mozilla-unified
   searching for changes
   adding changesets
   adding manifests
   adding file changes
   added 39 changesets with 309 changes to 235 files
   updated firefox tree tag beta (+2 commits)
   updated firefox tree tag esr52 (+2 commits)
   updated firefox tree tag inbound (+34 commits)
   updated firefox tree tag release (+1 commits)
   (run 'hg update' to get a working copy)

generaldelta and the Unified Repo
---------------------------------

The unified repository is encoded using Mercurial's *generaldelta*
storage mechanism. This results in smaller repositories and faster
repository operations.

.. important::

   Mercurial repositories created before Mercurial 3.7 did not use
   generaldelta by default. Pulling from the repository
   to a non-generaldelta clone will result in **slower** operations.

   It is highly recommended to create a new clone of the unified
   repository with Mercurial 3.7+ to ensure your client is
   using generaldelta.

To check whether your existing Firefox clone is using generaldelta::

   $ grep generaldelta .hg/requires

If there is no ``generaldelta`` entry in that file, you will need to
create a new repo that has generaldelta enabled. **Adding
``generaldelta`` to the requires file does not enable generaldelta on an
existing repo, so don't do it.** See :ref:`hgmozilla_common_upgrade_storage`
for instructions on how to do this.

incompatible Mercurial client; bundle2 required
-----------------------------------------------

Does this happen to you?::

   $ hg clone https://hg.mozilla.org/mozilla-unified firefox
   requesting all changes
   abort: remote error:
   incompatible Mercurial client; bundle2 required
   (see https://www.mercurial-scm.org/wiki/IncompatibleClient)

This message occurs when the Mercurial client is not speaking the modern
*bundle2* protocol with the server. For performance reasons, we require
*bundle2* to clone or pull the unified repository. This
decision is non-negotiable because removing this restriction could
result in excessive CPU usage on the server to serve data to legacy
clients.

If you see this message, one of the following is true:

* Your Mercurial client is too old. You should
  :ref:`upgrade <hgmozilla_installing>`.

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

Read `Mercurial's conflict docs <https://www.mercurial-scm.org/wiki/TutorialConflict>`_
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
