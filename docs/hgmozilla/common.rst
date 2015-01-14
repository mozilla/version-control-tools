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
