.. _mozreview_reviewboard:

=============================
Interacting with Review Board
=============================

The web interface of MozReview is powered by
`Review Board <https://www.reviewboard.org/>`_. This article will talk a
little about how Review Board works and how we've customized it for
MozReview.

How Review Board Works
======================

Before we go on to describe how to use Review Board, it is important
to have a brief understanding of how Review Board works.

For the patient, a read of the
`Review Board User Guide <https://www.reviewboard.org/docs/manual/2.0/users/>`_
is recommended.

For the impatient, some terminology. Note that some of these terms
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

Review Workflow
===============

We need to write this documentation. Until then, read the aforementioned
Review Board User Guide or go to https://reviewboard.mozilla.org/ and
tell us what parts aren't obvious.
