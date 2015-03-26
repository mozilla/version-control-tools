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

mozreview
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

  $ ./mozreview start /path/to/instance
  Bugzilla URL: http://192.168.59.103:57485/
  Review Board URL: http://localhost:57486/
  Mercurial URL: http://localhost:57487/
  Admin username: admin@example.com
  Admin password: password

You should be able to load the printed URLs in your browser and see a
working site. If you don't, file a bug!

.. warning::

   Storing MozReview instances inside a Mercurial repository will
   introduce many untracked files. It is recommended to store your
   instances outside of a repository checkout.

.. hint::

   All ``mozreview`` commands take a positional argument defining the
   path to the instance they should operate on. If you define the
   ``MOZREVIEW_HOME`` environment variable, you do not need to define
   this argument.

Creating Repositories
---------------------

MozReview instances are initially empty. They don't have any
repositories you can push to.

To create an empty repository to hold reviews, use mozreview::

   $ ./mozreview create-repo /path/to/instance repo_name

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
You'll probably want to set up a regular user account. Using mozreview:: 

   $ ./mozreview create-user /path/to/instance me@example.com password 'Joe Smith'

Stopping the Servers
--------------------

When you run ``mozreview start``, a number of Docker containers and
daemon processes will be started. These will linger forever - taking up
system resources - until there is some form of intervention.

The easiest way to stop everything related to the running MozReview
instance is to run ``mozreview stop``. e.g.::

   $ ./mozreview stop /path/to/instance

Interacting with Bugzilla
=========================

The ``bugzilla`` tool in the root of the repository provides a quick an
convenient interface to performing common Bugzilla operations, such as
creating bugs and printing the state of bugs.

This tool has the dual role of supporting both machines and humans. The
tests rely heavily on this tool to perform small, well-defined Bugzilla
interactions. You are encouraged to use the tool to help you hack on
MozReview.

Since the tool had its origins in testing land, it currently requires
environment variable(s) to define which Bugzilla instance to use.

If you have the ``MOZREVIEW_HOME`` variable set, the Bugzilla instance
associated with that MozReview instance is used. Else, you will need to
define the following variables:

BUGZILLA_URL
   This must be set the base URL of the Bugzilla instance you wish to
   communicate with.
BUGZILLA_USERNAME
   The username your API requests to Bugzilla will use.
BUGZILLA_PASSWORD
   The password your API requests to Bugzilla will use.

Interacting with Review Board
=============================

The ``reviewboard`` tool in the root of the repository provides a
mechanism to perform well-defined interactions with Review Board
instances. You are encouraged to use the tool to help you hack on
MozReview.

The tool had its origins in testing code, so its human interface could
use some use.

You'll need to define your Review Board credentials through environment
variables: ``BUGZILLA_USERNAME`` and ``BUGZILLA_PASSWORD``. The name
*bugzilla* is in there because MozReview shares its user database with
Bugzilla.

Code Locations
==============

``pylib/rbbz`` contains the modifications to Review Board to enable
Bugzilla integration and support for series of reviews.

``pylib/mozreview`` contains the UI modifications to Review Board.

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

Review Board Modifications
==========================

Review Request Extra Data
-------------------------

We store the following in the ``extra_data`` field of review requests:

p2rb
   String with value ``True``.

   The presence of this property differentiates review requests created
   by MozReview's special commit tracking code from ones created by
   vanilla Review Board. Many of our customizations to Review Board
   ignore review requests unless they have this annotation.

p2rb.is_squashed
   String with values ``True`` or ``False``.

   This property identifies whether this review request is a special
   *parent*/*squashed*/*tracking* review request.

   Since Review Board doesn't yet have the concept of multiple commits
   per review request, we needed to invent one. This property helps us
   distinguish the parent/tracking review request from its children.

p2rb.identifier
   String with user-supplied value.

   The value of this string groups multiple review requests belonging to
   the same logical review together. This property is defined on all
   our review requests and it should be the same for every review
   request tracked by a single *squashed*/*parent* review request.

p2rb.commits
   String of JSON serialization of an array of strings corresponding to
   review request IDs.

   This is set on *parent* review requests only.

   This array holds the list of review requests currently associated
   with this review request series.

p2rb.discard_on_publish_rids
   String of JSON serialization of an array of strings corresponding to
   review request IDs.

   This is set on *parent* review requests only.

   When drafts are created, sometimes extra review requests get created
   and associated with the *parent* review request but never actually
   get published (say you upload a commit by accident and then decide to
   remove it from review). There is no way to delete and recycle a
   review request, even if it has never been published. Instead, we
   track which review requests would become orphans. At publish time,
   we discard the drafts and review requests.

p2rb.unpublished_rids
   String of JSON serialization of an array of strings corresponding to
   review request IDs.

   This is set on *parent* review requests only.

   The list of review requests in this property tracks which review
   requests tracked by this *parent* review request should be published
   when the parent review request moves from *draft* to *published*
   state.

p2rb.commit_id
   String SHA-1 of the commit currently associated with this review
   request.


Running Tests
=============

The MozReview tests are all defined as part of the Mercurial extension.
To run the tests::

   $ ./run-mercurial-tests.py -j2 hgext/reviewboard/tests/*

Filing Bugs
===========

Found a bug in MozReview or want to create a bug to track an
improvement? File bugs against ``Developer Services :: MozReview``
at https://bugzilla.mozilla.org/enter_bug.cgi?product=Developer%20Services&component=MozReview.

Discussion
==========

General discussion on MozReview development and direction occurs on
our mailing list, `mozilla-code-review@googlegroups.com <mailto:mozilla-code-review@googlegroups.com>`_.

Submitting Changes
==================

See :ref:`devguide_contributing` for how to formulate and submit changes
for the ``version-control-tools`` repository.

Releasing Updates
=================

Want to release an update to MozReview? This section is for you.

Building eggs for Review Board Extensions
-----------------------------------------

If you modify ``mozreview``, ``rbbz`` or ``mozreview``, you'll need to produce
new Python eggs suitable for deployment on production.

We've provided a build environment in a Docker container to enable
building eggs. In addition, we have a high-level command that will start
the container, generate the eggs, retrieve them, and store them on the
local filesystem. To use::

  $ source venv/bin/activate
  $ DOCKER_STATE_FILE=.docker-state.json testing/docker-control.py build-reviewboard-eggs /path/to/output/directory
  Wrote /path/to/output/directory/mozreview-0.1.0alpha0-py2.6.egg
  Wrote /path/to/output/directory/rbbz-0.2.6-py2.6.egg

If you wish to use the Docker container, extract the image id from the
``build-reviewboard-eggs`` command output and invoke Docker like so::

  $ docker-control.py build-reviewboard-eggs .
  ...
  Successfully built 63b369dee3c4
  Generating eggs...
  Wrote ./mozreview-0.1.0alpha0-py2.6.egg
  Wrote ./rbbz-0.2.6-py2.6.egg
  $ docker run -it 63b369dee3c4 /bin/bash

You will find a virtualenv in ``/venv``. A copy of the
``version-control-tools`` repository is stored in
``/version-control-tools``. You can build eggs yourself by running
something like the following::

  $ source /venv/bin/activate
  $ cd /version-control-tools/pylib/rbbz
  $ python setup.py bdist_egg
