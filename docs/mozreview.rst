.. _mozreview:

==========================
Code Review with MozReview
==========================

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
``ssh://reviewboard.mozilla.org/hg/reviews/<repo>`` where ``<repo>`` is
the name of a repository. Valid names include ``firefox`` and
``version-control-tools``. An example ``.hg/hgrc`` fragment may look
like::

  [paths]
  default = https://hg.mozilla.org/mozilla-central
  default-push = ssh://hg.mozilla.org/mozilla-central

  review = ssh://reviewboard.mozilla.org/hg/reviews/firefox

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

  $ hg pullreviews

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
issues
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
   it.
   All review requests and reviews start in the draft state by default.
publishing
   The act of taking a draft review request or draft review and marking
   it as public, making it visible to everybody

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
and a link to the parent review request. The status of each review
request is surrounded in parenthesis.

Commit Message Formatting
-------------------------

The contents of commit messages are important to Review Board.

Currently, all reviews must be attached to a bug number. The Mercurial
extension will parse the commit messages, attempting to find a bug
number. The most recent bug number seen is used.

If a bug number is not found in any commits under review, an error will
be raised during ``hg push``. You can fix this be rewriting your commit
messages to contain a bug reference (e.g. *Bug 123 - Fix foo*), or you
can pass ``--reviewid`` to ``hg push``. e.g. ``hg push --reviewid 123``.
In this example, the review will be attached to bug 123.

**It is recommended to use proper commit messages instead of passing
--reviewid.**

The commit message will also be used to populate Review Board's fields
for the review request for that commit.

The summary of the review request will be the first line from the commit
message.

The description of the review request will be all subsequent lines.

**It is recommended to write a paragraph or two in the commit message to
explain the purpose of the commit.**


