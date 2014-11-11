.. _mozreview_creating:

========================
Managing Review Requests
========================

Initiating code review is very simple: just ``hg push``.  If you
have followed the
:ref:`installation instructions <mozreview_install>`, all you need to do
is type::

  $ hg push review

With no arguments, we assume you are trying to review the working copy
commit (``.``) and any of its parents that haven't landed yet.

.. note::

   MozReview handles reviewing multiple commits and has a single
   workflow no matter how many commits you are submitting for review.

.. hint::

   The selection of commits for review is equivalent to the Mercurial
   revset query ``::. and draft()``.

If you would like to control which commits are reviewed, you can pass ``-r
<rev>`` to specify an explicit *tip* and/or *base* commit.

With 1 revision specified, you define the *top-most* commit to be reviewed.::

  $ hg push -r 77c9ee75117e review
  or
  $ hg push -r 32114 review

With 2 revisions or a revset that evaluates to multiple revisions, you define
both the *base* and *tip* commits to review.::

  $ hg push -r 84e8a1584aad::b55f2b9937c7 review
  or
  $ hg push -r 520::524 review

.. hint::

   The 2 revision form is useful if you have multiple, distinct review series
   building on top of each other. You have a commit relying on changes made by
   an earlier one but you want to keep the reviews separate.

   The default selection of all non-public ancestors would include the parent
   commit(s) against your desires. Specifying an explicit base revision
   will keep your intentions clear.

If all goes well, Mercurial should print information about submitted
review requests. e.g.::

  $ hg push -r 2 review
  pushing to review
  searching for changes
  remote: adding changesets
  remote: adding manifests
  remote: adding file changes
  remote: added 1 changesets with 1 changes to 1 files (+1 heads)
  submitting 1 changesets for review

  changeset:  2:a21bef69f0d4
  summary:    Bug 123 - Implement foo
  review:     https://reviewboard.mozilla.org/r/8 (pending)

  review id:  bz://123/mynick
  review url: https://reviewboard.mozilla.org/r/7 (pending)
  (visit review url to publish this review request so others can see it)

.. important::

   You often need to log in to Review Board to publish the review.

   Review requests aren't published to the world by default (yet). If
   you need to take additional action to enable others to see the review
   requests, you will be alerted by the command output.

To learn how to manage the review requests in the Review Board web
interface, read :ref:`mozreview_reviewboard_publishing_commits`. Or,
continue reading to learn about how the Mercurial client and review
requests interact.

Review Identifiers
==================

Every push to MozReview must be associated with a *Review Identifier*
(*Review ID* for short).

.. important::

   MozReview currently requires that all review requests be associated
   with a non-confidential Bugzilla bug. Therefore, Review IDs must
   reference a bug.

If the commit message of a changeset pushed for review references a bug
number, a Review ID will be chosen for you automatically. The bug number
on the most recent commit will be used.

If a bug number if not found in any commits being considered for review,
an error will be raised during ``hg push``. You can avoid this by
rewriting your commit messages to contain a bug reference. Or, you can
pass ``--reviewid <reviewid>`` to ``hg push``. e.g. ``hg push --reviewid
123``.

.. tip::

    It is recommended to use proper commit messages instead of passing
    ``--reviewid``: you have to adjust your commit message before
    landing: you might as well get it out of the way early.

Updating Review Requests
========================

If you have previously pushed code for review and wish to update the
code that is being reviewed, the process is exactly the same as creating
a new review request: just ``hg push``.

Unless things have changed significantly, your previous review requests
should be updated with new versions of your code.

History Rewriting
=================

A common problem with code review tools is that they don't handle
history rewriting very well. A goal of MozReview is for this criticism
to not be levied at it. In this section, we'll talk a little about how
MozReview handles history rewriting.

Let's start with a simple example. Say you start with the following
changesets::

   500:2b9b330ed031 Bug 123 - Prep work for feature X
   501:61e7f5525241 Bug 123 - Implement feature X

You push these for review. They get assigned review requests 10 and 11,
respectively.

During the course of code review, someone asks you to perform more prep
work before the main feature commit. In other words, they want you to
insert a commit between ``500:2b9b330ed031`` and ``501:61e7f5525241``.
You refactor your commits via history rewriting (``hg histedit`` or some
such) and arrive at the following::

  500:2b9b330ed031 Bug 123 - Prep work for feature X
  502:7f825c52e03c Bug 123 - More prep work for feature X
  503:1833bbae416f Bug 123 - Implement feature X

You now push these for review. What happens?

Your minimal expectation should be that MozReview creates a new review
request to handle the newly-introduced commit. MozReview does indeed do
this. Added or removed commits will result in the review series being
expanded or truncated as necessary.

Your next expectation should be that MozReview appropriately maps each
commit to the appropriate pre-existing review request. In our example,
``500:2b9b330ed031`` would get mapped to review request 10 (simple
enough - nothing changed). In addition, ``503:1833bbae416f`` would get
mapped to review request 11 (because that commit is a logical successor
to ``501:61e7f5525241`` (which no longer exists because it was rewritten
into ``503:1833bbae416f``).

In its current implementation, MozReview should meet your expectations
and history rewriting should *just work* - rewritten commits and review
requests will automatically map to the appropriate former ones -
**provided you have obsolescence enabled**. If obsolescence is not
enabled, MozReview will perform index-based mapping. e.g. the first
commit will get mapped to the first review request, the second commit to
the second review request and so on. Added commits or removed commits
will impact review requests at the end of the series.

.. tip::

   Obsolescence markers result in automagical handling of history
   rewriting and are therefore highly recommended.

   To enable obsolescence markers, install the the
   `evolve extension <https://bitbucket.org/marmoute/mutable-history>`_.

.. note::

   There are plans to make the commit mapping more robust to cope with
   clients that don't yet have obsolescence enabled and to better
   support Git, which doesn't have a comparable feature to obsolescence.

Commit Message Formatting
=========================

The contents of commit messages are important to MozReview.

As mentioned earlier, commit messages are parsed to select the *Review
ID*. In addition, commit messages are also used to populate fields in
the Review Board web interface that will be used by reviewers and others
to summarize and describe the code being reviewed.

The first line of the commit message - the *summary line* - will be used
to populate the *Summary* field in Review Board.

All subsequent lines of the commit message will constitute the
*Description* field.

.. tip::

   It is recommended to write a multi-line commit message.

   Because the commit message is used to populate fields of a review
   request (including the summary and description), writing a multi-line
   commit message will save you time from having to fill out these
   fields later.

   Diffs of these fields are shown in the web-based review interface, so
   changes can be followed over time.

Looking Under the Covers
========================

Let's disect what happens when you run ``hg push review`` and the
follow-up actions so that you have a better understanding of some of the
magic involved.

When you type ``hg push review``, Mercurial first tries to resolve the
``review`` argument to a repository URL. Your ``.hg/hgrc`` file is
consulted and resolved to something like
``ssh://reviewboard-hg/firefox``.

Mercurial then opens a connection to that remote repositories and
discovers what local commits part of the requested review don't exist
on the remote and it pushes them.

Up until this point, everything is standard Mercurial behavior.

Once changes have been pushed to the remote repository, the
``reviewboard`` Mercurial extension you installed kicks into gear. It
sees that you have pushed to a repository that is capable of performing
code review. It assumes this is an intent to conduct code review
(otherwise why were you pushing to this repository).

The ``reviewboard`` Mercurial extension then collects information about
the pushed head and its ancestors. By default, it walks the parent commits
until it arrives at a commit that has the ``public`` phase (``published``
in Mercurial parlance). The range of commits between the pushed head and
the child of the last *published* commit form the review range: these
are all the commits that we are asking to review.

From this range of commits, we look at the commit messages. Our goal is
to find a bug number to associate the review against. We perform simple
pattern matching to find bug numbers. If we find multiple bug numbers,
we take the most recent bug number seen. If there are multiple bug
numbers in a commit message, we give weight to the first line (likely
appearing in the first line).

The found bug number along with your user identifier (your *ircnick*
setting) construct the *Review ID*. The *Review ID* is globally
unique and is used to identify this review for all of time.

Once the commits have been identified and a *Review ID* chosen,
Mercurial sends all this data to the remote Mercurial server in a
command that basically says *initiate a code review with these
parameters*.

The remote Mercurial server then takes this data and turns it into
review requests on Review Board. The result of this operation is
communicated back to the client - your machine - where a summary of the
result is printed.

