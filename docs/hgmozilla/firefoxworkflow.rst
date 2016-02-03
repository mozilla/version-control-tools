.. _hgmozilla_firefoxworkflow:

================
Firefox Workflow
================

This article outlines the **recommended** workflow for interacting
with the Firefox repository
(`mozilla-central <https://hg.mozilla.org/mozilla-central>`_ and its
derivatives).

Install Recommended Extensions
==============================

If you don't have Mercurial 3.7 or newer, install the
:ref:`bundleclone extension <hgmo_bundleclone>` to make clones faster
and more robust.

Installing the
`hgwatchman extension <https://bitbucket.org/facebook/hgwatchman>`_
will yield significant speed-ups on Firefox repositories. 1+ second
(70%) wall time reductions in ``hg status`` are common. This
extension should be universally enabled for an optimal Mercurial
experience.

Cloning the Repository
======================

Clone the Firefox repository by running::

   $ hg clone https://hg.mozilla.org/mozilla-central firefox
   $ cd firefox

Configuring Mercurial and the Clone
===================================

From your new clone, run ``./mach mercurial-setup`` to launch
an interactive wizard that will help you optimally configure
Mercurial for working with Firefox.

When prompted, it is highly recommended to install the
:ref:`firefoxtree extension <firefoxtree>`. The rest of these
instructions assume the *firefoxtree* extension is active.

Feature Development
===================

So you want to start work on a new Firefox feature? This section is
for you.

Start by obtaining the latest code so you aren't working on
old and possibly stale code::

   $ hg pull central

Then update to the tip of ``mozilla-central``::

   $ hg up central

.. note::

   These 2 commands require the *firefoxtree* extension to work
   properly.

Now, change some stuff. We assume you know how to do this.

Commit your changes::

   $ hg commit
   <type commit message in editor>

Make more changes and keep committing::

   $ hg commit
   <another commit message>

Push your changes to MozReview to initiate code review::

   $ hg push review

.. important::

   We assume you've followed the :ref:`mozreview_user` to configure
   MozReview.

OK. Progress on that feature is blocked waiting on review. It could
take a while for that to happen. Let's start working on something else::

   $ hg pull central
   $ hg up central
   <change stuff>
   $ hg commit
   <change stuff>
   $ hg commit
   $ hg push review

Changing Code After Reviews
---------------------------

A review comes back. Unfortunately review was not granted and you need
to make changes. No worries.

We need to find the changesets containing our feature so we can edit
them. Find the SHA-1s from MozReview, use a command like
``hg wip`` (see :ref:`hgmozilla_workflows`) to find them, or
``hg up`` directly to the bookmark you've given to the head::

   $ hg up <SHA-1 or label>

Now, you have several options available to you. If you know the changes
are small and won't conflict if reordered, go ahead and make them now
and commit::

   <make changes>
   $ hg commit
   <make more changes>
   $ hg commit

Then squash the changesets together::

   $ hg histedit

.. note::

   For ``hg histedit`` to work without arguments, you'll want to
   set the ``histedit.defaultrev`` config option to
   ``only(.)``.

You'll then need to:

1. Reorder your *fixup changesets* to occur immediately after (below)
   the changesets they will be modifying.
2. Set the action on these *fixup changesets* to ``roll`` so they
   are fully absorbed into the changeset that came before.

Alterantively, you can edit changes directly. Again, use ``hg histedit``.
But this time, change the action of the changesets you want to modify to
``edit``. Mercurial will print some things and will leave you with a
shell. The *working directory* will have been updated to the state of
the commit you are editing. If you run ``hg status`` or ``hg diff`` you
will see that this changesets's changes are applied to files already.
Make your changes to the files then run ``hg histedit --continue`` to
continue with the history editing.

.. note::

   Advanced users can use the
   `evolve extension <https://bitbucket.org/marmoute/mutable-history>`
   to edit changesets in place. Because this is still an experimental
   feature, it isn't documented here.

Once all the changes are made, you'll want to submit for review again::

   $ hg push review

Then we're back to waiting.

Reviewer Attribution and Landing
--------------------------------

You finally get review and can land your changes!

Update to the tip-most changeset that will land (often a head) after
finding the changesets using the technique in the previous section::

   $ hg up <SHA-1 or label>

Before landing, we need to rebase our unlanded changesets on top of
the latest changeset from an integration branch::

   $ hg pull inbound
   $ hg rebase -d inbound

If you need to add ``r=`` reviewer attribution to the commit message,
do that now::

   $ hg histedit

Change the action to ``m`` for all the changesets and proceed to
update commit messages accordingly.

And finally we land::

   $ hg push -r . inbound

.. note::

   MozReview will eventually perform the landing for you.
