.. _hacking_mozreview:

=================
Hacking MozReview
=================

Want to improve MozReview? This article will help you get started.

Before we begin, let's introduce the components that make up MozReview.

Review Board
   Django based code review software.

Mercurial Server
   Code reviews are initiated by pushing them to a Mercurial repository.

Bugzilla
   Review Board actions result in interaction with Bugzilla.

rbbz
   A Review Board extension that integrates Review Board with Bugzilla.

rbmozui
   A Review Board extension modifying the Review Board user interface.

Review Board Mercurial Extension
   There exist client-oriented and server-oriented Mercurial extensions
   to enable Mercurial peers to exchange and interface with review data.

Running a MozReview Instance
============================

It is possible to run a fully isolated, fully local MozReview instance
from your machine. This will give you an environment that should behave
like production.

To get started, you'll need to configure your environment. Run the
following::

   $ ./create-test-environment

This will create a virtualenv in ``venv/`` with all the necessary
package dependencies. It will also create Docker images for running
Bugzilla. This could take 10-20 minutes to run the first time you run
the command (most of the time is spent creating the Bugzilla Docker
image).

Now, you can create and start a MozReview instance::

   $ ./mach mozreview-start mozreview

The ``mozreview`` argument in that command is the path where we will
create and store MozReview data and state. It can be anywhere on the
filesystem. You may want to put it outside of the Mercurial clone so
``hg status`` doesn't report hundreds of untracked files.

If everything is successful, that command should print out details about
the running MozReview instance. e.g.::

  Bugzilla URL: http://192.168.59.103:57485/
  Review Board URL: http://localhost:57486/
  Mercurial URL: http://localhost:57487/
  Admin username: admin@example.com
  Admin password: password

You should be able to load the printed URLs in your browser and see a
working site. If you don't, file a bug!

Creating Repositories
---------------------

MozReview instances are initially empty. They don't have any
repositories you can push to.

To create an empty repository to hold reviews, use mach::

   $ ./mach mozreview-create-repo /path/to/mozreview repo_name

If all goes well, the URL of the newly-created repository should be
printed. You should then be able to ``hg push`` to that repository.
e.g.::

   $ hg push http://localhost:57487/repo_name

Remember to configure your client repository's hgrc to enable the Review
Board client extension and to set up proper Bugzilla credentials! Don't
worry, if something is wrong, the server will tell you during push.

Creating Users
--------------

MozReview instances initially only have a single user: the admin user.
You'll probably want to set up a regular user account. Using mach::

   $ ./mach mozreview-create-user /path/to/mozreview me@example.com password 'Joe Smith'

Stopping the Servers
--------------------

When you run ``mach mozreview-start``, a number of Docker containers and
daemon processes will be started. These will linger forever - taking up
system resources - until there is some form of intervention.

The easiest way to stop everything related to the running MozReview
instance is to run ``mach mozreview-stop``. e.g.::

   $ ./mach mozreview-stop mozreview

Code Locations
==============

``pylib/rbbz`` contains the modifications to Review Board to enable
Bugzilla integration and support for series of reviews.

``pylib/rbmozui`` contains the UI modifications to Review Board.

``hgext/reviewboard`` contains the client and server Mercurial
extensions.

``pylib/reviewboardmods`` contains the server-side code that runs as
part of pushing reviews to the Mercurial server. This contains the
low-level code that maps commits to review requests and ensures Review
Board review state is in a sane state. This code is logically part of
the Mercurial server extension. However, it exists in its own directory
so it can eventually be leveraged by Git and so it has a license that
isn't the GPL (Review Board isn't GPL - Mercurial is).

``pylib/mozhg`` contains some Mercurial support APIs used by the
Mercurial integration. This includes code for finding Bugzilla
credentials.

Running Tests
=============

The MozReview tests are all defined as part of the Mercurial extension.
To run the tests::

   $ ./run-mercurial-tests -j2 hgext/reviewboard/tests/*
