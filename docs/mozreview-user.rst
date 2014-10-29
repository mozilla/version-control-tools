.. _mozreview_user:

====================
MozReview User Guide
====================

This article is a guide on conducting code review at Mozilla using MozReview,
a repository-based code-review system based on
`Review Board <https://www.reviewboard.org/>`_.

For the quick and impatient who just want to look at the web interface,
it lives at https://reviewboard.mozilla.org/. Log in with your Bugzilla
credentials. Read on to learn how to create new review requests and to
conduct code review using the web interface.

Before you start code review, you need some code to review. This article
assumes you have at least basic knowledge of Mercurial and can create
commits that should be reviewed.

Please drill down into one of the following sections to continue.

.. toctree::
   :maxdepth: 2

   mozreview/install
   mozreview/review-requests
   mozreview/reviewboard
   mozreview/bugzilla

Filing Bugs
===========

Did you find a bug in MozReview? Do you have a feature request to make
it better? `File a bug <https://bugzilla.mozilla.org/enter_bug.cgi?product=Developer%20Services&component=MozReview>`_
in the ``Developer Services :: MozReview`` component.

.. tip::

   We like bug reports that contain command output!

   If you see an exception, stack trace, or error message, copy it into
   the bug.

   The tests for MozReview are implemented as a series of user-facing
   commands, simulating terminal interaction. If you give us the
   commands you used to cause the error, there's a good chance we can
   reproduce it and add a test case so it doesn't break.

.. _mozreview_getting_in_touch:

Getting in Touch
================

Have feedback or questions that aren't appropriate for bugs? Get in
touch with us!

If you prefer IRC, join ``#mozreview`` ``irc.mozilla.org``.

If you prefer email, send one to
`mozilla-code-review@googlegroups.com <mailto:mozilla-code-review@googlegroups.com>`_.
