.. _mozreview_creating:

========================
Creating Review Requests
========================

MozReview aims to be a natural extension of your version control tool.
As such, the first step to create review requests is to create commits
in your local clone/checkout of a repository.

Once commits are made, initiating code review is very simple: just
``hg push``. If you have followed the
:ref:`installation instructions <mozreview_install>`, all you need to do
is type::

  $ hg push review

With no arguments, we assume you are trying to review the current commit
and all of its ancestor commits that haven't landed yet.

For the simplest use cases, the workflow is simply:

1. commit
2. push
3. publish

Read on to learn about more features and advanced workflows.

Commit Message Formatting
=========================

The contents of commit messages are important to MozReview.

Summary and Description Fields
------------------------------

The Review Board web interface has *Summary* and *Description* fields
for each review request. These provide a simple, one-line *summary*
and more verbose, multi-line *description*, respectively.

The first line of the commit message - the *summary line* - will be
used to populate the *Summary* field in Review Board. All subsequent
lines of the commit message will constitute the *Description* field.

.. tip::

   It is recommended to write a descriptive, multiple line commit
   message.

   Descriptive commit messages can and should be used to let reviewers
   know what is happening with the commit. Review context should be
   part of the commit message, not something you type in later
   in the review interface.

   This is a better approach because it doesn't require you to switch
   contexts to your web browser to add the information, reviewers know
   to look in a consistent location for this info (the commit message),
   and because the information is preserved for all of time in the
   commit message, where it can be easily referenced later.

Specifying Reviewers in Commit Messages
---------------------------------------

Special syntax can be added to commit messages to specify the reviewers
for a commit. This syntax is ``r?<reviewer>`` where ``<reviewer>`` is a
MozReview username (which is typically the reviewer's Mozilla IRC
nickname).

For example, to request that ``gps`` review your commit, you would
format your commit message as such::

   Bug 123 - Fix type coercion in MozReview; r?gps

The commit message parser recognizes simple lists::

   Bug 123 - Fix type coercion in MozReview; r?gps, smacleod

The `test corpus <https://dxr.mozilla.org/hgcustom:version-control-tools/source/pylib/mozautomation/tests/test_commitparser.py>`_
demonstrates the abilities of reviewer parsing.

When commits are pushed for review, the server will parse the commit
message and assign reviewers as requested. This should *just work*.

.. important::

   ``r=`` for specifying reviewers, while supported, is not recommended
   and may result in a warning when submitting review requests.

   This is because ``r=`` is the syntax for denoting that review has
   been granted. Adding ``r=`` before review has been granted is
   effectively lying. MozReview doesn't want to encourage this practice,
   as it may result in confusion. Instead, the ``r?`` syntax should be
   used to denote that review is pending.

Commit Series
=============

MozReview handles reviewing multiple commits and has a single
workflow no matter how many commits you are submitting for review.

.. important::

   This is a significant difference between patch-based review tools
   like Bugzilla/Splinter. Since MozReview is tightly integrated with
   version control, things like ordering commits *just works* because
   the original commit data is obtained directly from a repository.

Choosing What Commits to Review
-------------------------------

When using ``hg push`` to push to the review repository, your client
will automatically select for review all *draft* changesets between
the working copy's commit and the first *public* ancestor. This is
equivalent to the Mercurial *revset* ``::. and draft()``. i.e.
``hg push review`` is equivalent to ``hg push -r '::. and draft()'``.

If you would like to control which commits are reviewed, you can pass ``-r
<rev>`` to specify a *revset* to select the commits that should be
reviewed.

With 1 revision specified, you define the *tip-most* commit to be reviewed.::

  $ hg push -r 77c9ee75117e review
  or
  $ hg push -r 32114 review

In this form, the specified commit and all of its *draft* ancestors will
be added to MozReview.

With 2 revisions or a revset that evaluates to multiple revisions, you
define both the *base* and *tip* commits to review.::

  $ hg push -r 84e8a1584aad::b55f2b9937c7 review
  or
  $ hg push -r 520::524 review

.. hint::

   The 2 revision form is useful if you have multiple, distinct review series
   building on top of each other. You have a commit relying on changes made by
   an earlier one but you want to keep the reviews separate.

   The default selection of all non-public ancestors would include the parent
   commit(s) in addition to the ones you wanted. Specifying an explicit
   base revision will keep your intentions clear and prevent multiple
   series from interfering with each other.

For the special case where you only want to review a single changeset,
the ``-c`` argument can be used to specify a single changeset to review.::

  $ hg push -c b55f2b9937c7 review

.. tip::

   You only need to specify ``-c`` to *cherry-pick* a commit out of a
   larger series of *draft* changesets.

Review Identifiers
------------------

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

After The Push
==============

If all goes well, the output of ``hg push`` to a review repository should
look something like this::

  $ hg push -r a21bef69f0d4 review
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
  (visit review url to publish these review requests so others can see them)

The first first lines of the output is the standard output from
Mercurial when you push. The lines that follow are from MozReview:
it tells you how your changesets mapped to review requests and a
brief summary of the state of those review requests.

.. important::

   You often need to log in to Review Board to publish the review.

   Review requests aren't published to the world by default (yet). If
   you need to take additional action to enable others to see the review
   requests, you will be alerted by the command output.

To learn how to manage the review requests in the Review Board web
interface, read :ref:`mozreview_reviewboard_publishing_commits`. Or,
continue reading to learn about how the Mercurial client and review
requests interact.

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
