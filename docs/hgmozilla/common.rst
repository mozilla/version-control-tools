.. _common:

=======================
Performing Common Tasks
=======================

Revive a Commit That Was Backed Out
===================================

Say your repository has the following history::

   changeset:   263002:dfc93c68f9c7
   user:        Gijs Kruitbosch <gijskruitbosch@gmail.com>
   date:        Mon Dec 22 15:05:06 2014 +0000
   summary:     Bug 1113299 - hide tab mirroring feature if unavailable, r=jaws

   changeset:   263001:268dfa4925ec
   user:        Brian Grinstead <bgrinstead@mozilla.com>
   date:        Tue Jan 13 12:25:57 2015 -0800
   summary:     Backed out changeset 291e3a83a122 (bug 1042619)

   changeset:   263000:492134f929e2
   user:        Tim Nguyen <ntim.bugs@gmail.com>
   date:        Tue Jan 13 09:51:00 2015 -0500
   summary:     Bug 1121048 - Add back round corners on perf tool icon glyphs. r=jsantell

Commit ``291e3a83a122`` was backed out by ``263001:268dfa4925ec`` and
you want to *revive* it, either to reland it or to work on it again.

``hg graft`` should be used to revive old commits. In this case::

   $ hg graft -f 291e3a83a122
   grafting 262999:291e3a83a122 "Bug 1042619 - Change 'width x height' letter x to × in devtools frontend;r=bgrins"
   merging browser/devtools/canvasdebugger/canvasdebugger.js
   merging browser/devtools/layoutview/view.js
   merging browser/devtools/responsivedesign/responsivedesign.jsm

   $ hg log
   changeset:   263004:3c6672d2df85
   tag:         tip
   parent:      263002:dfc93c68f9c7
   user:        Aaron Raimist <aaronraimist@protonmail.ch>
   date:        Tue Jan 13 11:59:01 2015 -0800
   summary:     Bug 1042619 - Change 'width x height' letter x to × in devtools frontend;r=bgrins

As you can see, ``hg graft`` recreated the original commit. The
``merging`` lines in the output above indicate that Mercurial invoked
its merge resolution algorithm to as part of grafting. What this means
is that the listed files were changed between when the commit was
originally performed and where the new commit resides. Mercurial was
able to automatically merge the differences. Had it not been able to do
so, it would entered the merge resolution workflow and asked you to run
``hg graft --continue`` to finish the graft.

.. note::

   The ``-f`` in this example is important: it allows grafting of commits
   that are already ancestors of their destination. Without it, Mercurial
   sees that you are attempting to recreate a commit that has already been
   applied and will prevent you from probably shooting yourself in the
   foot.

If you are familiar with Git, ``hg graft`` is roughly equivalent to
``git cherry-pick``.

Upgrading Repository Storage
============================

Mercurial periodically makes changes to its on-disk storage that require
a one-time *upgrade* of repository data to take advantage of the new
storage format. Mercurial doesn't do this automatically because the
backwards compatibility guarantees of Mercurial say that the version of
Mercurial that created a repo should always be able to read from it, even
if common repo operations are performed by a newer version.

You have 2 options for upgrading repository storage::

1. Re-clone the repo
2. Run ``hg debugupgraderepo``

Upgrading Storage via Clone
---------------------------

A fresh Mercurial clone will usually use optimal/recommended storage for
the Mercurial version being used. However, depending on how the clone is
performed and where it is cloned from, this may not always work as
expected.

To achieve an optimal clone with efficient storage, **always
clone from https://hg.mozilla.org/ - not from a local repo**. By cloning
from hg.mozilla.org, your clone will inherit the optimal storage
used by the server. If you clone from anywhere else, you may inherit
sub-optimal storage.

Say you have a copy of *mozilla-central* in a local *mozilla-central*
directory. Perform a clone-based upgrade by running the following::

   # Grab pristine copy of repo.
   $ hg clone -U https://hg.mozilla.org/mozilla-central mozilla-central.new

   # Copy over .hgrc
   $ cp mozilla-central/.hg/hgrc mozilla-central.new/.hg/hgrc

   # Pull your unpublished work from your local clone into the new clone.
   $ hg --config phases.publish=false -R mozilla-central.new pull mozilla-central

   # Now rename/remove your repos as appropriate.

.. important::

   That config adjustment for ``phases.publish=false`` is important. Without it,
   *draft* changesets will become *public* and Mercurial won't let you edit them.
   To guard against, it is a good practice to add the following to your per-repo
   ``.hg/hgrc`` file immediately after a clone::

       [phases]
       publish = false

   If you accidentally *publish* your *draft* changesets, you can reset phases by
   running the following commands::

       # Reset all phases to draft.
       $ hg phase --draft --force -r 0:tip

       # Synchronize phases from a publishing repo.
       $ hg pull https://hg.mozilla.org/...

Upgrading Storage via ``debugupgraderepo``
------------------------------------------

*(Requires Mercurial 4.1 or newer)*

Upgrading repository storage in-place is relatively easy: just use
``hg debugupgraderepo``. This command (which is strictly still an
experimental command but shouldn't corrupt your data) essentially
does an in-place ``hg clone`` while applying various data and storage
optimizations along the way. **The command doesn't make any permanent
changes until the very end and makes a backup of your original data,
so there should be a low risk of data loss.**

In its default mode of execution, ``hg debugupgraderepo`` simply
converts storage to the latest storage format: it doesn't heavily
process data to optimize it. So, to get the benefits of data optimization
(which will shrink the size of the repo and make operations faster),
you need to pass some flags to the command.

The first time you upgrade a repo, run as follows::

   $ hg debugupgraderepo --optimize redeltaparent --optimize redeltamultibase --run

``redeltaparent`` tells Mercurial to recalculate the internal deltas
in storage so a logical parent is used. The first time this runs, it
will significantly slow down execution but it can result in significant
space savings on a Firefox repos. If you specify this on a repo where
data is already efficiently stored, it is almost a no-op.

``redeltamultibase`` tells Mercurial to calculate for merges against
both parents and to use the smallest. This always adds significant
processing time to repos with lots of merges. It can also drastically
reduce the repository size (by several hundred megabytes for Firefox
repos).

On a Firefox repository, it could take 2-3 hours to perform data
optimizations if the repository isn't already optimized. If you
clone from hg.mozilla.org, you will get these optimizations
automatically because the server performs them.
