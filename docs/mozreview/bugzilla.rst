.. _mozreview_bugzilla:

====================
Bugzilla Integration
====================

MozReview and the Review Board web interface are tighly integrated with
Bugzilla.

Shared User Database and Authentication
=======================================

Review Board shares its user database with Bugzilla.

Logging into Review Board is done through Bugzilla.  The *Log in* link
in Review Board will redirect you to Bugzilla, where you should
provide your usual Bugzilla credentials. Note that if you have an
active Bugzilla session, you will automatically be redirected back to
Review Board without having to provide your credentials again.

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

When someone leaves a review on a review request, the chosen flag
value will be set in Bugzilla (or cleared if the empty value is
chosen).

If a new revision of a commit is pushed up to MozReview, a new
attachment will not be created. Rather, any ``r-`` and cleared review
flags on the original Bugzilla attachment will be reset to ``r?``.
Any existing ``r+`` flags will be left as is, that is, the review is
carried forward. This last part is under discussion and may change in
the future. There is also work under way to allow explicitly
re-requesting review even if a ``r+`` has previously been granted.

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
