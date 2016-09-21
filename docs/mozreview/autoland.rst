.. _mozreview_autoland:

=============================
Landing Commits with Autoland
=============================

MozReview provides an easy way to land commits to another repository
through a service called Autoland.  Autoland can send your commits to
the repository of record when your reviews have been granted.  In
addition, Autoland can be used to send commits to Try if you are
developing within mozilla-central (e.g. Gecko or Firefox).

Sending Commits to Try
======================

If you are working on Gecko, Firefox, or anything else within
mozilla-central, and if you have at least L1 SCM access, you can send
your commits to the Try service at any time.  On the Reviews view of
any review request there is an Automation menu.  If you have L1 access
or greater, the top option, "Trigger a Try Build", will be enabled for
you.  Note that it doesn't matter which review request in a given series
you are on; all commits in the current series will be sent to Try.

This option will open a dialog prompting for a Try string, with an expandable
panel for the TryChooser Syntax Builder tool.  Once a build is started,
results will be visible under the commits table in all review requests
in the series, with links to Mercurial and Treeherder.

Landing Commits
===============

Once your commits have been reviewed, if you have L3 SCM access you
can use Autoland to push them to the repository of record.  For
Gecko/Firefox, this is mozilla-inbound.  As with Try builds, the
Autoland option is in the Automation menu, as "Land Commits".

For the Autoland option to be enabled, the current user must have L3
access **and** the following must be true for every commit in the series:

* The commit has been reviewed by someone with L3 access, **or**
* The commit has been submitted (pushed to MozReview) by someone with
  L3 access.

If these conditions have been met, the option will be enabled.
Clicking it will prompt the user to confirm the commit message(s), which
will be rewritten to reflect the actual reviews given,
e.g. ``r=reviewer``.  Review strings requesting reviews,
e.g. ``r?reviewer``, will be stripped out.  In the case that the
commit message is not correct, the author will have to push up an
amended commit or land directly.

As with Try landings, the entire commit series will be landed
regardless of the commit on which the "Land Commits" action is
triggered. Results, with links to Mercurial and Treeherder, will be
posted to the review requests as soon as the commit has landed.  If
for some reason Autoland cannot land the commits due to a transient
error, e.g. due to the tree being closed, it will retry until it is
successful.
