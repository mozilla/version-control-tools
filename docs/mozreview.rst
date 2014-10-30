.. _mozreview:

=====================================
MozReview: Mozilla's Code Review Tool
=====================================

*MozReview* is a code review platform tightly integrated with Mozilla's
infrastructure to provide a code review experience optimized for
developer productivity.

.. toctree::
   :maxdepth: 2

   mozreview-user
   hacking-mozreview

Status
======

MozReview soft launched on October 29, 2014. The soft launch means:

* We are encouraging early adoptors and select groups to start using it.
* We commit to not mass-deleting data or making major
  backwards-incompatible changes.
* We expect to make major changes that may significantly alter
  appearances and/or workflows.

In the spirit of *perfect is the enemy of good*, MozReview launched
with many rough edges and unimplemented features. If you find
something that is obviously wrong or seems bad, chances are we know
about it. Most of the energy to this point has been spent on shipping
something, not shipping the perfect solution.

We've spent a lot of energy making it easy to hack on MozReview so
anyone can come along and improve it. For more, read
:ref:`hacking_mozreview`. We've spent a lot of time on a robust and
comprehensive :ref:`testing infrastructure <testing>` so we can move
fast and not break things.

Known Issues and Limitations
----------------------------

* Errors on the *Commits* page don't always result in UI. This is an
  upstream bug and is tracked in
  `bug 1088823 <https://bugzilla.mozilla.org/show_bug.cgi?id=1088823>`_.

* The Web UI around modifying and interacting with the review series
  leaves a lot to be desired.
  `Bug 1064111 <https://bugzilla.mozilla.org/show_bug.cgi?id=1064111>`_
  tracks improvement it.

* Review Board supports publishing and reviewing images and screenshots.
  This is broken.
  `Bug 1056858 <https://bugzilla.mozilla.org/show_bug.cgi?id=1056858>`_
  tracks.

Planned Features
----------------

There are many features that we know people want and need. Here is a
partial list:

* Git support. We only support Mercurial right now because it is the
  canonical version control tool for Firefox and because it is easier to
  extend Mercurial to perform productivity-enhancing magic.

* Enhanced integration with Bugzilla. The two-way interaction between
  Review Board and Bugzilla could be improved. For example, the comments
  posted to Bugzilla could be better formatted and could contain better
  details.

* Automatically updating Review Board and Bugzilla when changes land. If
  you land code that was tracked in a Review Board review, we want the
  Review Board review requests to be closed automatically.
