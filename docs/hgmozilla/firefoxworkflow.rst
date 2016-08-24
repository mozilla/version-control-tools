.. _hgmozilla_firefoxworkflow:

================
Firefox Workflow
================

This article outlines the **recommended** workflow for interacting
with the Firefox repository
(`mozilla-unified <https://hg.mozilla.org/mozilla-unified>`_.

Optimally Configure Mercurial
=============================

When you run ``bootstrap.py`` or ``mach bootstrap`` (if you already have a
clone), the bootstrapper will prompt you to run a Mercurial configuration
wizard. You should run this wizard and make sure it is happy about your
Mercurial state.

You should also run `mach bootstrap` periodically to ensure Mercurial
support files are up-to-date.

.. important::

   The instructions in this article assume the
   :ref:`firefoxtree extension <firefoxtree>` is installed. Please activate
   it when the wizard prompts you to!

Cloning the Repository
======================

Clone the Firefox repository by running::

   $ hg clone https://hg.mozilla.org/mozilla-unified firefox
   $ cd firefox

Feature Development
===================

So you want to start work on a new Firefox feature? This section is
for you.

Start by obtaining the latest code so you aren't working on
old and possibly stale code::

   $ hg pull

Then update to the tip of ``mozilla-central``::

   $ hg up central

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
take a while for that to happen. Let's start working on something else. We
always start by pulling the latest code so our change isn't out of date before
we've event started.::

   $ hg pull
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

   For ``hg histedit`` to work without arguments, you'll need Mercurial
   3.7 or newer.

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

Autolanding
-----------

You finally get review and can land your changes!

The easiest way to do this is through the use of Autoland. You can access
Autoland through the ``Land Commits`` option of the ``Automation`` menu.
Clicking this button displays a dialog containing a list of commits to be
landed. MozReview will attempt to automatically rewrite the commit messages
to reflect who reviewed which commit. If everything looks good, click the
``OK`` button and the autolander will land your commits for you.

Autoland will attempt to rebase you commits on the head of mozilla-inbound
for you automatically. If a manual rebase is required, an error will be
displayed in MozReview and you will have to rebase yourself.

.. note::

   We do not currently have plans to support an integration branch other
   that ``mozilla-inbound``. In the future, we hope to remove integration
   branches so we end up with a merge free history.

If Autoland succeeds, *Pulsebot* will comment in your bug that your
changes have landed. Unfortunately, there is not currently any notification
that Autoland has failed outside of MozReview, so if the trees are open
and your changes have not landed within a few minutes, please check back
in MozReview to see if any errors have occurred.


Manual Reviewer Attribution and Landing
--------------------------------

Unable to use Autoland? Follow these instructions.

Update to the tip-most changeset that will land (often a head) after
finding the changesets using the technique in the previous section::

   $ hg up <SHA-1 or label>

Before landing, we need to rebase our unlanded changesets on top of
the latest changeset from an integration branch::

   $ hg pull
   $ hg rebase -d inbound

If you need to add ``r=`` reviewer attribution to the commit message,
do that now::

   $ hg histedit

Change the action to ``m`` for all the changesets and proceed to
update commit messages accordingly.

And finally we land::

   $ hg push -r . inbound
