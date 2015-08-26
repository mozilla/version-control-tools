.. _mozreview_install:

=========================================
Configuring Your Machine to Use MozReview
=========================================

Installing the Mercurial Extension
==================================

Interacting with MozReview from Mercurial **requires** a Mercurial
extension to be installed and configured.

To install that extension, clone the
`version-control-tools <https://hg.mozilla.org/hgcustom/version-control-tools>`_
repository and activate the ``hgext/reviewboard/client.py`` extension in
your ``hgrc``. For example::

  $ hg clone https://hg.mozilla.org/hgcustom/version-control-tools ~/version-control-tools
  $ cat >> ~/.hgrc << EOF
  [extensions]
  reviewboard = ~/version-control-tools/hgext/reviewboard/client.py
  EOF

.. tip::

   If you already have a Firefox repository like
   `mozilla-central <https://hg.mozilla.org/mozilla-central>`_ cloned, you
   can run ``mach mercurial-setup`` and the guided wizard will prompt you
   for code review settings. Follow the prompts and this configuration
   will be done for you.

.. note:: The Mercurial extension requires Mercurial 3.0 or above.

   Running the most recent released version of Mercurial is strongly
   recommended. New major releases come out every 3 months. New minor
   releases come every month.

   As of November 2014, Mercurial 3.2 is the most recent and recommended
   version.

   If you are running an older Mercurial, please obtain a modern version
   from the `official project page <http://mercurial.selenic.com/>`_.

Configuring the Mercurial Extension
===================================

The *reviewboard* Mercurial extension requires some configuration before
it can be used.

Bugzilla Credentials
--------------------

Mozilla's Review Board deployment uses
`Mozilla's Bugzilla deployment <https://bugzilla.mozilla.org/>`_ (BMO)
for user authentication and authorization. In order to talk to Review
Board, you will need to provide valid Bugzilla credentials.

Bugzila credentials consist of a Bugzilla username (email address)
and API key. To obtain an API key:

1. Visit https://bugzilla.mozilla.org/userprefs.cgi?tab=apikey in your
   browser.
2. Generate a new API key
3. Add your username/email and API key to your hgrc file.

A template to put in your hgrc file is as follows::

  [bugzilla]
  ; Your Bugzilla username. This is an email address.
  username = me@example.com
  ; A Bugzilla API key
  apikey = ojQBGzhDmFYRFSX4xWNCSyOEsJKqisU0l0EJqXh6

IRC Nickname
------------

The Mercurial extension and Review Board uses your IRC nickname as an
identifier when creating reviews. You'll need to define it in your
Mercurial config file. Add the following snippet to an ``hgrc`` file
(likely the global one at ``~/.hgrc`` since your IRC nick is likely
global)::

  [mozilla]
  ircnick = mynick

Don't worry if you forget this: the extension will abort with an
actionable message if it isn't set.

.. note:: This requirement will eventually go away.

   Don't worry, the extension will tell you if your configuration needs
   updating.

Review Repositories
===================

The Mercurial extension initiates code review with Review Board by
pushing changesets to a special code review repository that is attached
to ``MozReview``.

There are multiple code review repositories, one per *canonical*
repository.

Unless you like typing full URLs every time you push, you will want
to configure a *path* in your ``hgrc`` file.

Simple Configuration
--------------------

If you push to ``ssh://reviewboard-hg.mozilla.org/autoreview``, your
client will automatically figure out which review repository to push to.
It doesn't matter which repository you are using: if there is a review
repository configured, things will *just work*. If a review repository
is not known, the push will fail.

To configure the *auto review* repository, add an entry for this URL
under the ``[paths]`` section of your ``~/.hgrc`` or ``.hg/hgrc`` file.
We recommend the name ``review``. e.g.::

   [paths]
   review = ssh://reviewboard-hg.mozilla.org/autoreview

.. warning::

   Attempting to push to the ``autoreview`` repository without configuring
   the Mercurial extension (see above) will likely result in your client
   attempting to push all history to the ``autoreview`` repository. The
   server will reject the push, but not until all data has been transferred.
   For Firefox repositories, this could take several minutes and consume
   over a gigabyte of bandwidth!

Advanced Configuration
----------------------

If the *auto review* repository is too much magic for you, you can
define the review URL for each repository you wish to review from.

You will want to define a named path in your per-repository ``.hg/hgrc``
to the code review Mercurial repository. We recommend the name
``review``. The URL for the repository should be
``ssh://reviewboard-hg.mozilla.org/<repo>`` where ``<repo>`` is
the name of a repository. You can find the list of available repositories
at https://reviewboard-hg.mozilla.org/. Just swap ``https://`` with
``ssh://``.

An example ``.hg/hgrc`` fragment may look like::

  [paths]
  default = https://hg.mozilla.org/hgcustom/version-control-tools
  default-push = ssh://hg.mozilla.org/hgcustom/version-control-tools

  review = ssh://reviewboard-hg.mozilla.org/version-control-tools

.. tip::

   If you have the `firefoxtree <firefoxtree>`_ Mercurial extension installed
   and are working on a Firefox repository, you don't need to define the
   ``review`` path: it is automatically defined when operating on a Firefox
   repository.

Updating SSH Config
===================

You will want to configure your SSH username for
``reviewboard-hg.mozilla.org``. See :ref:`auth_ssh` for instructions.

.. tip::

   If you have already configured ``hg.mozilla.org`` in your SSH config,
   just copy the settings to ``reviewboard-hg.mozilla.org``.

As of December 2014, the SSH fingerprint for the RSA key is
``a6:13:ae:35:2c:20:2b:8d:f4:8d:8e:d7:a8:55:67:97``.

Host Fingerprint in hgrc
========================

Mercurial allows you to declare key fingerprints in your hgrc.

If you are running Python 2.7.9 or newer (run ``hg debuginstall``
to see what version of Python Mercurial is using - it may not be
the Python you expect), Mercurial will automatically verify that
certificates chain to a trusted certificate authority (CA).

If you are running Python 2.7.8 or older, Python doesn't do these
checks and will print warnings when connecting to hosts whose
fingerprints aren't defined. To silence these warnings, or to
explicitly declare the host fingerprint (a protection against
spoofing by a certificate issued by another trusted CA), add
the following to your ``~/.hgrc``::

   [hostfingerprints]
   reviewboard-hg.mozilla.org = 1b:62:0b:40:35:87:bd:28:5a:a1:43:ce:c8:e6:c0:2f:d0:7f:b6:c3

Now that your client is all configured, it is time to conduct some code
review. Continue reading the :ref:`mozreview_user`.
