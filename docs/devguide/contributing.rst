.. _devguide_contributing:

============
Contributing
============

Find a bug? Interested in contributing a bug fix or enhancement? Read
on!

Filing Bugs
===========

Bugs against software in this repository can be filed in the
`Developer Services <https://bugzilla.mozilla.org/enter_bug.cgi?product=Developer%20Services>`_
Bugzilla product. The component should be obvious. If you are unsure,
use *General*.

Contacting Us
=============

The people that maintain the code in this repository lurk in the
following IRC channels on ``irc.mozilla.org``:

#vcs
   Where everybody who maintains all the version control properties
   hangs out.
#mozreview
   Where developers and users of MozReview lurk.

Just pop in a channel, ask a question, and wait for someone to answer.
The channels can be quiet for hours at a time, so please stick around
if nobody replies at first.

Submitting Patches for Review
=============================

We use :ref:`MozReview <mozreview>` for conducting code review. Follow
the :ref:`mozreview_user` to configure your Mercurial client. Then, ``hg
push ssh://reviewboard-hg.mozilla.org/version-control-tools`` to
initiate the code review process.

Before submitting patches for review, please :ref:`run the tests
<devguide_testing>` and verify things still work. Please also read the
following section on how to optimally create commits.

Commit Creation Guidelines
--------------------------

We prefer many, smaller and focused commits than fewer, larger commits.
Please read `Phabricator's Recommendations on Revision Control <https://secure.phabricator.com/book/phabflavor/article/recommendations_on_revision_control/>`_
and apply the *One Idea Per Commit* practice to patches to this
repository. Please also read their article on
`Writing Reviewable Code <https://secure.phabricator.com/book/phabflavor/article/writing_reviewable_code/>`_
and tailor your commits appropriately.

It is recommended for commits to this repository to have the following
commit message convention::

   component: short description (bug xyz); r=reviewer

   A sentence explaining the purpose of the patch. Another sentence
   adding yet more detail.

   Another paragraph adding yet more detail. We really like context to
   exist in our patches rather than elsewhere.

The first line of the commit message begins with the component the patch
is touching. Run ``hg log`` and see what others have used if you don't
know what to put here. The short description should be pretty obvious.

If the patch is tracked in a bug, please enclose the bug in parenthesis
at the end of the commit message. **This is different from the Firefox
convention.** We do things differently because we want the beginning of
the commit message to emphasize the thing that was changed. This
improves discovery when filtering through commit messages, as it allows
you to easily and cheaply find all commits that changed a specific
component. Furthermore, we prefer to work with the mentality of code,
not bugs, being first. We defer the bug to the end of the summary line
to reflect that.

Bug and Review Requirements
---------------------------

**We do not require that every commit have a bug association.** If there
isn't a bug on file, please don't waste time filing one just to write a
patch.

**We do not require that every commit be reviewed.**

Please abide by the following rules before pushing without a bug or
review:

* **A review is required** if you are modifying code that runs on a
  production service or we install or recommend installing on a
  user's machine (MozReview, Mercurial extensions, Mercurial hooks,
  etc).

* If you are adding new test code and you know what you are doing, you
  may **not** need a review. This exception is a little fuzzy around
  tests for production code (reviews are helpful to ensure the tests are
  accurate and proper).

* If you are adding or hacking on a miscellaneous tool that doesn't
  have test coverage or isn't widely used or relied upon, you may
  **not** need a review.

* You do **not** need a review to update documentation. If something is
  wrong, just fix it.

* When in doubt, ask someone on ``#vcs`` if you need a review before
  pushing.

Pushing Commits
===============

When pushing commits to
``ssh://hg.mozilla.org/hgcustom/version-control-tools``, it is important
for you to set the ``@`` bookmark to the new tip.

Say you've created a new head or bookmark for your commit series.
Assuming the working directory of your repository is on the commit you
wish to make the new repository tip, here is how you should land your
changes::

  $ hg pull
  pulling from default
  requesting all changes
  adding changesets
  adding manifests
  adding file changes
  added 2 changesets with 2 changes to 1 files
  updating bookmark @

  $ hg rebase -d @
  $ hg bookmark @
  moving bookmark '@' forward from abcdef012345

  $ hg push -B @
  pushing to default
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  added 2 changesets with 2 changes to 4 files
  exporting bookmark @

If you fail to update the remote ``@`` bookmark, nothing bad should
happen. So don't worry too much if you forget to do it from time to
time.

If you do forget, just perform a ``hg push -B @`` any time to update the
remote bookmark. You can do this if you have no new changesets to push.
