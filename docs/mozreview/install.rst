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
   `mozilla-central <https://hg.mozilla.org/mozilla-central>`_, clones, you
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

If no configuration is defined, the *reviewboard* extension will
automatically try to find Bugzilla credentials by looking for a login
cookie in Firefox profiles on your machine. If it finds one, it will try
to use it.

If you would like to explicitly define credentials to use, copy the
following Mercurial configuration snippet into your global ``~/.hgrc``
or per-repository ``.hg/hgrc`` file and adjust to your liking::

  [bugzilla]
  ; Your Bugzilla username. This is an email address.
  username = me@example.com
  ; Your Bugzilla password (in plain text)
  password = MySecretPassword

  ; or

  ; Your numeric Bugzilla user id.
  userid = 24113
  ; A valid Bugzilla login cookie.
  cookie = ihsLJHF308hd

You will likely need to go snooping around your browser's cookies to
find a valid login cookie to use with ``userid`` and ``cookie``.
``userid`` comes from the value of the ``Bugzilla_login`` cookie and
``cookie`` comes from the value of the ``Bugzilla_logincookie`` cookie.

.. note:: Using cookies over your username and password is preferred.

   For security reasons, it is recommended to use cookies instead of
   password for authentication. The reason is that cookies are transient
   and can be revoked. Your password is your *master key* and it should
   ideally be guarded.

   Bugzilla and Review Board will eventually support API tokens for an
   even better security story.

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

Per-Repository Configuration
============================

The Mercurial extension initiates code review with Review Board by
pushing changesets to a special code review repository that is attached
to ``MozReview``.

There are multiple code review repositories. There is typically one per
repository that wishes to have code reviewed.

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

.. note:: Upcoming autodiscovery of repositories

   It is a planned feature to have the Mercurial extension automatically
   discover and use the appropriate code review repository. This will
   alleviate the requirement of setting a repository path in your
   ``hgrc`` file.

Updating SSH Config
===================

You will want to configure your SSH username for
``reviewboard-hg.mozilla.org``. See :ref:`auth_ssh` for instructions.

.. tip::

   If you have already configured ``hg.mozilla.org`` in your SSH config,
   just copy the settings to ``reviewboard-hg.mozilla.org``.

As of December 2014, the SSH fingerprint for the RSA key is
``a6:13:ae:35:2c:20:2b:8d:f4:8d:8e:d7:a8:55:67:97``.

Now that your client is all configured, it is time to conduct some code
review. Continue reading the :ref:`mozreview_user`.
