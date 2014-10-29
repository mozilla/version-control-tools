.. _mozreview_bugzilla:

====================
Bugzilla Integration
====================

MozReview and the Review Board web interface are tighly integrated with
Bugzilla.

Shared User Database and Authentication
=======================================

Review Board shares its user database with Bugzilla.

Your Review Board login credentials are your Bugzilla email address and
password.

Your Review Board username is derived from your name in Bugzilla. If you
are using the ``Firsname Lastname [:ircnick]`` convention, your Review
Board username will be your IRC nickname, ``ircnick`` in this example.

Forms that accept users in Review Board all accept email addresses, IRC
nicknames, full names, and Review Board usernames.

Review Flags
============

Asking a user for review on Review Board will create an attachment on the
associated Bugzilla bug and will set the ``review`` flag to ``?`` to
request review from the specified user. Clicking on the attachment in
the Bugzilla user interface or following the link to the review will
redirect you to Review Board.

If someone gives a *Ship It* on a review request, a ``review+`` will be
set in Bugzilla.

Review Comments
===============

Review comments will be turned into Bugzilla comments when reviews are
published. The full content of the review comment will be reflected in
Bugzilla.

.. note::

   The existing Bugzilla comment format is far from optimal and will
   likely change.

   We are even considering removing low-level comments from Bugzilla
   completely. All options are on the table. If you have ideas on what
   things should look like, please
   :ref:`get in touch <mozreview_getting_in_touch>`.
