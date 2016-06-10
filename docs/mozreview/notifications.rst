.. _mozreview_notification:

====================
Change Notifications
====================

Pulse Notifications
===================

MozReview will send messages to
`Pulse <https://wiki.mozilla.org/Auto-tools/Projects/Pulse>`_ after
certain events occur.

Pulse messages are written to the
`exchange/mozreview/ <https://tools.taskcluster.net/pulse-inspector/#!((exchange:exchange/mozreview/,routingKeyPattern:%23))>`_
exchange.

The routing key identifies the message type. Each message type is described
in the sections below.

mozreview.commits.published
---------------------------

This message is sent when commits are published for review. This occurs
when new commits are sent to Review Board for review. The message
contains the following keys:

parent_review_request_id
   Integer review request id of the parent review request tracking all
   commits in the review series.
parent_diffset_revision
   Integer identify the revision of the diffset for this event.
commits
   Array containing metadata for each commit in this series. See
   below for the contents of each entry.
repository_url
   The URL of the repository where the commits submitted for review are
   located.
landing_repository_url
   The URL of the repository where commits will get pushed to to land.
review_board_url
   URL of Review Board. Use this to construct URLs for API requests to
   get more details of what changed.

Each entry in ``commits`` is an object containing the following keys:

rev
   Commit identifier (likely a 40 character SHA-1 hash).
review_request_id
   Integer review request this commit is being reviewed in.
diffset_revision
   Integer revision for the diffset of the review request tracking
   this commit.

mozreview.review.published
--------------------------

This message is sent when a review or review reply is published. e.g.
when someone grants review, leaves a comment, etc.

Instances of this message have the following keys:

review_id
   Integer of unique identifier for this review.
review_time
   Integer seconds since UNIX timestamp that this review occurred.
review_username
   String username of the person performing the review action.
review_request_id
   Integer review request this review is associated with.
review_request_bugs
   Array of bug identifiers associated with the review request.
   This will almost certainly be Bugzilla bug numbers.
review_request_participants
   Array of string usernames of people participating in this review
   request.
review_request_submitter
   String username of the person who submitted the review request.
review_request_target_people
   Array of string usernames of people who have been asked to review
   this review request.
repository_id
   Integer of the repository this review request is associated with.
repository_bugtracker_url
   URL pattern of the URL to an individual bug. This will likely be
   ``https://bugzilla.mozilla.org/show_bug.cgi?id=%s``.
review_board_url
   URL of Review Board. Use this to construct URLs for API requests to
   get more details of what changed.