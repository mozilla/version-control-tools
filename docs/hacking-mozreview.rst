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
  waiting for Bugzilla to start
  Bugzilla accessible on http://192.168.59.104:55568/
  Bugzilla URL: http://192.168.59.104:55568/
  Review Board URL: http://192.168.59.104:55569/
  Mercurial URL: http://192.168.59.104:55570/
  Pulse endpoint: 192.168.59.104:55573
  Autoland URL: http://192.168.59.104:55574/
  Admin username: admin@example.com
  Admin password: password
  LDAP URI: ldap://192.168.59.104:55571/
  HG Push URL: ssh://192.168.59.104:55572/

  Run the following to use this instance with all future commands:
    export MOZREVIEW_HOME=/Users/gps/tmp/mozreview

  Refresh code in the cluster by running:
    ./mozreview refresh

  Perform refreshing automatically by running:
    ./mozreview autorefresh

  (autorefresh requires `watchman`)

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

   The remainder of this document assumes this environment variable
   is defined.

Creating Repositories
---------------------

MozReview instances are initially empty. They don't have any
repositories you can push to.

To create an empty repository to hold reviews, use ``mozreview``::

   $ ./mozreview create-repo repo_name
   HTTP URL (read only): http://192.168.59.104:55570/repo_name
   SSH URL (read+write): ssh://192.168.59.104:55572/repo_name

Pushing to repositories is done via SSH, as this is how production
works.

Creating Users
--------------

There are two primary account systems inside the MozReview cluster:
Bugzilla and LDAP.

Bugzilla accounts provide authentication and authorization for
web properties, including Bugzilla, MozReview, and Autoland.

LDAP accounts hold information needed to communicate with the
Mercurial SSH server.

The two account systems are completely separate.

Review Board also has its own account system. But it is linked
to Bugzilla's user database and should be thought of an extension
rather than a separate account system.

LDAP Accounts
^^^^^^^^^^^^^

In order to speak to the SSH server, you'll need to create an
LDAP account and configure it with an SSH key.

.. note::

   This workflow is a bit complicated and should be improved.

SSH accounts are managed via LDAP. So, creating an LDAP user is
equivalent to configuring SSH access. Run the ``create-ldap-user``
sub-command to create an LDAP user with an existing SSH key::

  $ ./mozreview create-ldap-user gszorc@mozilla.com gps 2002 'Gregory Szorc' --key-file ~/.ssh/id_rsa --scm-level 3

Here, we create the account ``gszorc@mozilla.com`` with system user
name ``gps`` with user ID ``2`` with name ``Gregory Szorc`` with an
existing RSA SSH keypair and with level 3 source code access.

.. note::

   When specifying an existing key file, the public key will be
   added to the LDAP server running in the cluster. Your private key
   remains as a secret on your local machine.

You'll likely want your LDAP/SSH username to be shared with your
login name for hg.mozilla.org. This is to make your Mercurial SSH
configuration simpler. If the usernames are shared, you can add
something like the following to your ``hgrc``::

  [ui]
  ssh = ssh -l gszorc@mozilla.com

This tells Mercurial to use a specified login name for all SSH
connections.

Alternatively, edit your ``~/.ssh/config`` file and specify an
alternate ``User`` for the Docker host.

Bugzilla Accounts
^^^^^^^^^^^^^^^^^

MozReview clusters are provisioned with a single admin user by default.
Credentials for this user are printed during ``mozreview start``.

You'll almost certainly want to create a regular, non-admin user.
This can be done with the ``create-user`` sub-command::

   $ ./mozreview create-user me@example.com password 'Joe Smith'

Refreshing Code
---------------

Because processes are running inside Docker containers and are operating
on copies of code, changes to the source code in your working directory
will not automatically take effect in running processes.

To refresh code running on the cluster, run the ``refresh``
sub-command::

   $ ./mozreview refresh

The ``autorefresh`` command can be used to start a file watching
daemon that will automatically refresh the cluster when local files
are changed::

   $ ./mozreview autorefresh

.. tip::

   Use of ``autorefresh`` is highly recommended when doing development,
   as it will save you the overhead of having to manually type a refresh
   command every time you change something.

Stopping the Servers
--------------------

When you run ``mozreview start``, a number of Docker containers and
daemon processes will be started. These will linger forever - taking up
system resources - until there is some form of intervention.

The easiest way to stop everything related to the running MozReview
instance is to run ``mozreview stop``. e.g.::

   $ ./mozreview stop

Exporting Environment Variables
-------------------------------

Many support tools (``bugzilla``, ``reviewboard``, etc) look for magic
environment variables to configure things like what server to talk to.

The ``shellinit`` sub-command can be used to mass export all variables
defining how a MozReview cluster works::

   $ $(./mozreview shellinit)

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
use some love.

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
