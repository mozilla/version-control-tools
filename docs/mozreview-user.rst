.. _mozreview_user:

====================
MozReview User Guide
====================

This article is a guide on conducting code review at Mozilla using MozReview,
a repository-based code-review system based on
`Review Board <https://www.reviewboard.org/>`_.

Getting Started
===============

Before you start code review, you need some code to review. This article
assumes you have at least basic knowledge of Mercurial and can create
commits that should be reviewed.

Installing the Mercurial Extension
----------------------------------

We have authored a Mercurial extension to make the process of submitting
code reviews to Mozilla as easy as possible. To install that extension,
clone the
`version-control-tools <https://hg.mozilla.org/hgcustom/version-control-tools>`_
repository and activate the ``hgext/reviewboard/client.py`` extension in
your ``hgrc``. For example::

  $ hg clone https://hg.mozilla.org/hgcustom/version-control-tools ~/version-control-tools
  $ cat >> ~/.hgrc << EOF
  [extensions]
  reviewboard = ~/version-control-tools/hgext/reviewboard/client.py
  EOF

Alternatively, if you are working out of a Firefox repository like
`mozilla-central <https://hg.mozilla.org/mozilla-central>`_, you can run
``mach mercurial-setup`` and the guided wizard will prompt you about
code review settings and take care of setting up the environment
automatically.

.. note:: The reviewboard extension requires Mercurial 3.0 or above.

   Running the most recent released version of Mercurial is strongly
   recommended. New major releases come out every 3 months. New minor
   releases come every month.

   As of November 2014, Mercurial 3.2 is the most recent and recommended
   version.

Configuring the Mercurial Extension
-----------------------------------

The *reviewboard* Mercurial extension requires some configuration before
it can be used.

Bugzilla Credentials
^^^^^^^^^^^^^^^^^^^^

Mozilla's Review Board deployment uses
`Mozilla's Bugzilla deployment <https://bugzilla.mozilla.org/>`_ (BMO)
for user authentication and authorization. In order to talk to Review
Board, you will need to provide valid Bugzilla credentials.

If no configuration is defined, the *reviewboard* extension will
automatically try to find Bugzilla credentials by looking for a login
cookie in Firefox profiles on your machine. If it finds one, it will try
to use it.

If you would like to explicitly define credentials to use, copy the
following Mercurial configuration snippet into your global ``~/.hgrc``
or per-repository ``.hg/hgrc`` file and adjust to your liking::

  [bugzilla]
  ; Your Bugzilla username. This is an email address.
  username = me@example.com
  ; Your Bugzilla password (in plain text)
  password = MySecretPassword

  ; or

  ; Your numeric Bugzilla user id.
  userid = 24113
  ; A valid Bugzilla login cookie.
  cookie = ihsLJHF308hd

You will likely need to go snooping around your browser's cookies to
find a valid login cookie to use with ``userid`` and ``cookie``.
``userid`` comes from the value of the ``Bugzilla_login`` cookie and
``cookie`` comes from the value of the ``Bugzilla_logincookie`` cookie.

.. note:: Using cookies over your username and password is preferred.

   For security reasons, it is recommended to use cookies instead of
   password for authentication. The reason is that cookies are transient
   and can be revoked. Your password is your *master key* and it should
   ideally be guarded.

   Bugzilla and Review Board will eventually support API tokens for an
   even better security story.

IRC Nickname
^^^^^^^^^^^^

The Mercurial extension and Review Board uses your IRC nickname as an
identifier when creating reviews. You'll need to define it in your
Mercurial config file. Add the following snippet to an ``hgrc`` file
(likely the global one at ``~/.hgrc`` since your IRC nick is likely
global)::

  [mozilla]
  ircnick = mynick

Don't worry if you forget this: the extension will abort with an
actionable message if it isn't set.

Defining the Code Review Repository
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The Mercurial extension initiates code review with Review Board by
pushing changesets to a special repository that is attached to
Review Board.

You will want to define a named path in your per-repository ``.hg/hrc``
to the code review Mercurial repository. We recommend the name
``review``. The URL for the repository should be
``ssh://reviewboard-hg.mozilla.org/<repo>`` where ``<repo>`` is
the name of a repository. Valid names include ``firefox`` and
``version-control-tools``. An example ``.hg/hgrc`` fragment may look
like::

  [paths]
  default = https://hg.mozilla.org/mozilla-central
  default-push = ssh://hg.mozilla.org/mozilla-central

  review = ssh://reviewboard-hg.mozilla.org/firefox

.. note:: Upcoming autodiscovery of repositories

   It is a planned feature to have the Mercurial extension automatically
   discover and use the appropriate code review repository. This will
   alleviate the requirement of setting a repository path in your
   ``hgrc`` file.

Testing the Configuration
-------------------------

Now that the Mercurial extension is installed and configured, you'll
need to test it. From your repository's directory, simply run the
following::

  $ hg fetchreviews

If that prints a message like *updated 27 reviews* and exits without
spewing an error, everything is configured properly and you are ready to
submit code for review!

How Review Board Works
======================

Before we go on to describe how to conduct code reviews, it is important
to have a brief understanding of how Review Board works.

For the patient, a read of the
`Review Board User Guide <https://www.reviewboard.org/docs/manual/2.0/users/>`_
is recommended.

For the impatient, some terminology.  Note that some of these terms
are specific to MozReview.

review request
   A request to review a single patch/diff/commit
review
   Responses to a review request
issue
   A component of a review that is explicitly tracked as part of the
   review request
review request series
   A collection of review requests all belonging to the same logical
   group
parent review request
   For review request series, the review request that tracks the
   overall state of the series
draft
   Refers to a state review requests or reviews can be in where content
   is not publicly visible and is only available to the person who created
   it. All review requests and reviews start in the draft state by default.
publishing
   The act of taking a draft review request or draft review and marking
   it as public, making it visible to everybody
ship it
   This is the term used for *granting review* or *r+* in Bugzilla
   terminology.
review id
   A unique identifier identifying a review request series. This is
   commonly derived from a bug number and username.

Pushing Code for Review
=======================

Initiating code review is very simple; just push::

  $ hg push review

If no arguments are specified, the working copy's commit and all its
unpublished ancestors will be considered for review.

If you would like to control which commits are reviewed, specify ``-r
<rev>``. e.g.::

  $ hg push -r 77c9ee75117e review
  or
  $ hg push -r 32114 review

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

You should see a summary of the changesets that were pushed for review
and a URL to the parent review request. The status of each review
request is surrounded in parenthesis.

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

Commit Message Formatting
=========================

The contents of commit messages are important to Review Board.

Currently, all reviews must be attached to a bug number. The Mercurial
extension will parse the commit messages, attempting to find a bug
number. The most recent bug number seen is used.

If a bug number is not found in any commits under review, an error will
be raised during ``hg push``. You can fix this be rewriting your commit
messages to contain a bug reference (e.g. *Bug 123 - Fix foo*), or you
can pass ``--reviewid`` to ``hg push``. e.g. ``hg push --reviewid 123``.
In this example, the review will be attached to bug 123.

.. tip:: It is recommended to use proper commit messages instead of passing --reviewid.

The commit message will also be used to populate Review Board's fields
for the review request for that commit.

The summary of the review request will be the first line from the commit
message.

The description of the review request will be all subsequent lines.

.. tip:: It is recommended to write a multiline commit message.

   Because the commit message is used to populate fields of a review
   request (including the summary and description), writing a multiline
   commit message will save you time from having to fill out these
   fields later.

   Diffs of these fields are shown in the web-based review interface, so
   changes can be followed over time.

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
You refactor your commits via history rewriting (``hg histedit``) and
arrive at the following::

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
