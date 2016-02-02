.. _mozreview_commits:

===============================================
Creating Commits and Submitting Review Requests
===============================================

MozReview aims to be a natural extension of your version control tool.
You create commits in version control then submit those commits for
code review.

A commit that has been submitted to MozReview is referred to as a
*review request*. Commits submitted together are grouped together in
the MozReview web interface.

Before we describe how commits are submitted, it is important to
learn how commits should be authored.

How to Structure Commits
========================

Commits are Reviewed (and Landed) as They are Authored
------------------------------------------------------

Local commits are submitted to MozReview (and eventually landed) as-is.

Contrast this behavior to other code review tools which can collapse
local commits into a single diff (e.g. Phabricator and Review Board)
or put emphasis on the end-to-end diff (e.g. GitHub).

There are some important implications to this model:

* Reviewers see exactly the commits you author locally.
* *Fixup* commits aren't appropriate for submitting to MozReview
  (they should be rewritten/folded/squashed before submission).
* Each commit should be complete and standalone. You should not
  break something in one commit and fix it in the next commit because
  that would break *bisect* operations on the final repo history.

Prefer More, Smaller Commits Over Large, Monolithic Commits
-----------------------------------------------------------

Performing code review is hard.

In general, code review becomes even harder the more content that is
changed in a commit (because the reviewer has more to look at).

Reviewing a single diff that changes hundreds or even thousands of
lines is a daunting and time-consuming task. Furthermore, the more that
is changed, the higher the chances that there will be something that
is wrong. The more iterations between reviewer and author there are,
the longer it takes for changes to land and the longer others have to
wait for progress to be made.

For these reasons and more, it is recommend to author more, smaller
commits than fewer, larger commits. This practice is sometimes referred
to as *microcommits*. In general, a commit should be as small as
possible but no smaller. Here are some guidelines:

* If you need to perform some cleanup before a refactor, put the cleanup
  in its own commit separate from the refactor.
* If you need to fix a typo, put that in its own commit.
* If you need to make a wide-sweeping change such as adding an
  argument to a commonly-called function, update function declarations
  one at a time (1 per commit) or use 1 commit to introduce the new
  *interface* and another for implementing it.

Write Detailed Commit Messages
------------------------------

It is recommended to write descriptive, multiple line commit
messages that explain **why** you are making a change.

Descriptive commit messages should be used to let reviewers
know what is happening with the commit and the reason for it.
Without this information, reviewers might have to spend extra time
figuring it out for themselves.

Since you just authored the commit, the *why* and *how* should be
known to you, so you shouldn't have to exert that much energy writing
a commit message.

If a commit is fixing a bug, the commit message is an excellent
location to summarize the state and history of the bug. This is
especially true if the bug has dozens or more comments and/or is
complicated. A good commit message fixing a bug should not require
the reviewer to reference that bug as part of performing the review.

If nothing else, detailed commit messages are forever recorded in
your repository's history. Your version control tool has functionality
to search commit messages. So having a detailed commit message could
help people find history easier (e.g. references to other bugs).

No Merge Commits
----------------

Reviewing merge commits is wonky because the diff of a merge commit
is ambiguous and can be deceiving. Furthermore, many projects using
MozReview attempt to keep repository history as linear as possible
(read: no merge commits) because linear history is easier to reason
about and makes operations like *bisect* simpler.

**Therefore MozReview refuses to submit merge commits for review.**
If you attempt to submit a merge commit for review, you will see an
error.

You can use merge commits in the development of your code. However,
a single range of commits submitted for review must not contain a
merge commit.

Formatting Commit Messages to Influence Behavior
================================================

When you submit commits to MozReview, commit messages are parsed
for special syntax that influences behavior.

If you have contributed patches to Mozilla before, parts of this
syntax should be known to you as it has been used at Mozilla for
several years. However, it is important to read this section so you
are informed of MozReview's *extensions* to this syntax.

Summary and Description Fields
------------------------------

The MozReview web interface has *Summary* and *Description* fields
for each review request. These provide a simple, one-line *summary*
and more verbose, multi-line *description*, respectively.

The first line of the commit message - the *summary line* - will be
used to populate the *Summary* field in Review Board. All subsequent
lines of the commit message will constitute the *Description* field.

Specifying Reviewers in Commit Messages
---------------------------------------

Reviewers for submitted commits can be specified using a special
syntax on the first line of the commit message.

This syntax is::

   r?<reviewer>

Where ``<reviewer>`` is a MozReview username. The MozReview username
is derived from the ``[:ircnick]`` syntax from the Bugzilla full
name field.

The ``r?`` means *review requested*.

For example, to request that ``gps`` review your commit, you would
format your commit message as such::

   Fix type coercion in MozReview; r?gps

The commit message parser recognizes simple lists::

   Fix type coercion in MozReview; r?gps, smacleod

The `test corpus <https://dxr.mozilla.org/hgcustom_version-control-tools/source/pylib/mozautomation/tests/test_commitparser.py>`_
demonstrates the abilities of reviewer parsing.

When commits are pushed for review, the server will parse the commit
message and assign reviewers as requested. This should *just work*.

.. important::

   ``r=`` for specifying reviewers, while supported, is not recommended
   and may result in a warning when submitting review requests.

   This is because ``r=`` is the syntax for denoting that review has
   been *granted*. Adding ``r=`` before review has been granted is
   effectively lying. MozReview doesn't want to encourage this practice,
   as it may result in confusion. Instead, the ``r?`` syntax should be
   used to denote that review is pending.

   Autoland will automatically rewrite ``r?`` to ``r=`` when landing
   commits, so using ``r?`` should be no extra work for you.

Bug References
--------------

Commit messages may reference Bugzila bugs.

If the first line of a commit message references a bug, the review
request for that commit message is linked to that bug.

The following are examples of common bug reference formats::

   Bug 123 - Fix type coercion in MozReview
   Fix type coercion in MozReview (bug 123)

Bug References, Review Identifiers, and Grouping Commits
========================================================

Now that you understand how to author commits and format commit
messages, let's talk about how commits are translated to review requests
on MozReview.

.. important::

   It is critical to understand this section. You may want to read
   it multiple times.

Commits are submitted to MozReview as a group. The group can be as
small as a single commit or as large as you need it to be.

Commits submitted together are grouped together in the MozReview
web interface. See an
`example table of commits/review requests <https://reviewboard.mozilla.org/r/28807/>`_

Each commit has its own *review request* and URL. These are URLs
ending in ``/r/<number>``.

Commits are grouped together using something called the *Review
Identifier* or *Review ID*. Currently, each review request *must*
be associated with a Review ID.

The Review ID is currently derived from a user-specified *username*
and the first bug number referenced in the series of commits.

Most of the time, Review IDs are hidden and silently enable grouping
of commits without issue. However, they can be the source of many
problems.

At this time, Review IDs must be globally unique on MozReview.

Since Review IDs are derived from your username and the first bug
number referenced in the submitted commits, a duplicate Review ID
can be automatically selected. This can lead to problems such as
overwriting an existing group of review requests with unrelated
commits.

Since Review IDs are required and since Review IDs are derived from
bug numbers referenced in commit messages, if commits being submitted
don't reference a bug number, an error will be raised because no
Review ID could be derived. Simply rewrite the commit message to
contain a bug reference and a Review ID should be derived automatically.

.. note::

   Review IDs are a side effect of some early implementation decisions.
   We would like to eventually phase them out and enable more powerful
   workflows.

Submitting Commits for Review
=============================

Commits are submitted for review by using your version control tool.

Using Mercurial
---------------

Initiating code review with Mercurial is as simple as ``hg push``.
If you have followed the :ref:`installation instructions <mozreview_install>`,
you configured the ``review`` path and all you need to type is::

   $ hg push review

With no arguments, this will submit the current commit ``.`` and all
unpublished ancestor commits for review. For most workflows, this is
typically what is desired.

Choosing Which Commits to Submit
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

By default, ``hg push review`` will submit for review all commits
matching the *revset* ``::. and draft()``. In other words,
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

Using Git
---------

Initiating code review with Git requires the ``git mozreview`` command.
See its :ref:`installation instructions <mozreview_install_git>`.

Once you have your local Git repo configured to use MozReview, submitting
to MozReview is performed via::

   $ git mozreview push

This command behaves almost exactly the same as the equivalent Mercurial
command.

Choosing Which Commits to Submit
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

By default, ``git mozreview push`` will submit for review ``HEAD`` and
all its ancestors not existing on any known remote ref.

To control which commits are submitted for review, specify a commit-ish
or revision range (e.g. ``HEAD~2..HEAD`` or ``7accd95..6834f7e``) of commits
to review as an additional command argument. e.g.::

   $ git mozreview push HEAD~2..HEAD

If a single commit is specified, a single commit will be submitted for review.
If a range is specified, the behavior is the same as selecting commits via
``git log`` or ``git rev-list``. See the Git help/man pages for more.

Publishing Review Requests
==========================

The output of your command to submit commits to MozReview should look
something like the following::

    pushing to review
    searching for appropriate review repository
    redirecting push to ssh://reviewboard-hg.mozilla.org/version-control-tools
    searching for changes
    remote: adding changesets
    remote: adding manifests
    remote: adding file changes
    remote: added 3 changesets with 1 changes to 14 files (+1 heads)
    remote: recorded push in pushlog
    submitting 3 changesets for review

    changeset:  6716:2aa6647caff6
    summary:    testing: install git-cinnabar in testing environment; r=smacleod
    review:     https://reviewboard.mozilla.org/r/31127 (draft)

    changeset:  6717:5d16eb8f4544
    summary:    reviewboard: allow fake ids file path to be passed in; r=dminor
    review:     https://reviewboard.mozilla.org/r/31859 (draft)

    changeset:  6739:6a236cefb4ad
    summary:    git-mozreview: git command for interacting with MozReview (bug 1153053); r?glandium, dminor, smacleod
    review:     https://reviewboard.mozilla.org/r/6863 (draft)

    review id:  bz://1153053/gps
    review url: https://reviewboard.mozilla.org/r/6861 (draft)

    publish these review requests now (Yn)?  y
    (published review request 6861)

The last part of this output contains a list of commits that have been
submitted for review.

``(draft)`` indicates that the MozReview review requests are in a *draft*
state. (The opposite of *draft* is *published*.) Changes in a draft state
are only visible to the person who made them.

By default, most changes in MozReview go into a draft state and must be
explicitly published. This gives the author the opportunity to verify
everything is fine before letting others see the changes. Perhaps you
accidentally submitted something you didn't want to submit. As long as
that submission stayed in the draft state, nobody saw the mistake and
nobody was confused except you. You can simply submit again overwriting
the old, wrong drafts with the new, correct ones.

Review requests can be published from the URLs printed. Unless you are
submitting a complicated update to an existing group of commits, you
are probably fine just telling the interactive prompt that you would
like to publish from the command line.

Once review requests are published, others can see them! If you have
requested review from someone, they would have received an e-mail
notification that they have a pending review request. It's now time
for you to sit back and wait for their review!

Submitting Updated Commits for Review
=====================================

Nobody is perfect. Reviewers will inevitably say you need to change
something in your code and re-submit the review request. How should
you do this?

The process for updating review requests with new commits is exactly
the same as submitting new commits. If all goes according to plan,
your rewritten commits map up to their previous versions and the
reviewer sees the new diffs!

.. danger::

   There are some scenarios where updates to existing commits don't
   map cleanly to existing review requests. This can result in a
   horrible experience that will make you contemplate not using
   MozReview. Read on for details.

Understanding How Commits are Mapped to Review Requests
-------------------------------------------------------

A review request in MozReview tracks the evolution of a single logical
commit in version control. For example, say you have 3 commits:

1. Implement foo
2. Implement bar
3. Implement baz

The first time you submit this series of 3 commits for review, MozReview
will allocate 3 review requests, 1 for each commit. Let's give them
review request numbers 11, 12, and 13.

The reviewer looks at these commits and tells you (for whatever
reason) to implement *bar* before *foo*. So, you perform some local
history rewriting and reorder commits 1 & 2. Our commits now look like:

1. Implement bar
2. Implement foo
3. Implement baz

Distributed version control tools (except Mercurial with changeset
evolution - more on this later) don't really track logical commits -
they track content. In reality, commits are represented as SHA-1
hashes of their content. In effect, commit identifiers are random.
This means that tracking the same logical commit (e.g. *Implement foo*)
through history rewriting is a non-exact science. It must be based on
heuristics (such as commit message or diff similarity) or some other
tracking mechanism.

Mercurial's experimental changeset evolution feature is one such
tracking mechanism. Unlike vanilla Mercurial or Git, this feature
records that commit Y is a logical successor to commit X. Basically,
when commit X is seen, Mercurial knows that Y is a newer version of it
and should be used instead.

.. important::

   MozReview doesn't yet make an attempt to intelligently map old
   commits to their new versions using heuristics.

   This means that reordering, inserting, or dropping commits can
   result in review requests getting mapped to different logical
   commits.

Unless you have Mercurial's changeset evolution feature enabled,
the behavior of MozReview to map commits to review requests is
very simple: review requests and commits are paired in their existing
topological order.

For example, you have 2 commits, X and Y. These are allocated
review requests 20 and 21 when first submitted. You make updates to both
and re-submit. X' is allocated to 20 and Y' to 21. Nothing unexpected there.

Now you add a new commit, Z. When you submit the series of X', Y', Z,
X' is allocated to 20, Y' to 21, and a new review request - 22 - is created
for Z. This also *just works*.

But what happens when you remove X'? We now have Y'' and Z'. Since 20 is
the first available review request, Y'' goes to 20 and Z' goes to 21. 22
is left unused and is discarded. Comments about X and X' linger on 20,
which is now tracking Y''. This is horribly sub-optimal.

Avoiding Pitfall When Rewriting History
---------------------------------------

As the above section demonstrates, the lack of heuristics for
mapping logical commits to existing review requests can result in
badness.

While this sounds like a massive deficiency in MozReview, in practice
people tend to learn to work around it by not practicing workflows that
result in things getting in a wonky state. (Again, yes, we need to
implement the heuristics so the tracking is better.)

The easiest way to avoid issues with history rewriting is to use
Mercurial's changeset evolution feature by installing the
`evolve extension <https://bitbucket.org/marmoute/mutable-history>`_.
The tracking it performs *just works*. It will change your Mercurial
workflow significantly and will likely be a bit confusing initially.
But people tend to love it once they get over the steep learning
curve (it's no worse than Git's learning curve).

If you don't want to use Mercurial + changeset evolution, you can work
around the limitation by not inserting or removing commits at the
beginning or middle of a commit series. As long as the offsets of commits
within a series remain constant, MozReview will keep mapping commits
to the same review request. If you keep adding commits to the end, these
will be dealt with properly as well.

Of course, commit series consisting of a single commit don't have any
issues with offset remapping, so there is nothing to worry about there.
