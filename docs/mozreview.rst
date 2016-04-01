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

Known Issues and Limitations
============================

Please see the `open bugs for MozReview <http://mzl.la/1sHkGHM>`_. Some
notables include:

Planned Features
================

There are many features that we know people want and need. Many items
are tracked in the `open bugs list <http://mzl.la/1sHkGHM>`_. In
addition, some high-level features that we want to build:

* Git support. We only support Mercurial right now because it is the
  canonical version control tool for Firefox and because it is easier to
  extend Mercurial to perform productivity-enhancing magic.

* Enhanced integration with Bugzilla. The two-way interaction between
  Review Board and Bugzilla could be improved. For example, the comments
  posted to Bugzilla could be better formatted and could contain better
  details
