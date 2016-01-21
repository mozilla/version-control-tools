.. _mozreview_install_mercurial:

======================================
Configuring Mercurial to Use MozReview
======================================

Wizard-Based Configuration
==========================

If you already have a Firefox repository like
`mozilla-central <https://hg.mozilla.org/mozilla-central>`_ cloned, you
can run ``mach mercurial-setup`` from it and a guided wizard will walk
you through configuring Mercurial for optimal use on Mozilla projects.
Configuring Mercurial for MozReview is part of this wizard.

.. important::

   The wizard currently does not configure the ``autoreview``
   repository. See :ref:`mozreview_install_autoreview` for how to do
   this manually.

If you don't have a Firefox repository, have no fear: just follow the
instructions below.

Manual Configuration
====================

Installing the Mercurial Extension
----------------------------------

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

.. note::

   You likely already have an ``[extensions]`` section in your Mercurial
   configuration. Run ``hg config --edit --global`` (or ``hg config -e
   -g`` for short) to open your global configuration in an editor and
   add the aforementioned extension under the ``[extensions]`` section.

Configuring the Mercurial Extension
-----------------------------------

The Mercurial extension requires additional Mercurial configuration file
options before it can be used.

Bugzilla Credentials
^^^^^^^^^^^^^^^^^^^^

You will need to define your BMO credentials in your Mercurial
configuration in order to authenticate with MozReview. These are placed
under the ``[bugzilla]`` section in your configuration file. Again,
``hg config -e -g`` to open an editor and place something like the
following in your config file::

  [bugzilla]
  ; Your Bugzilla username. This is an email address.
  username = me@example.com
  ; A Bugzilla API key
  apikey = ojQBGzhDmFYRFSX4xWNCSyOEsJKqisU0l0EJqXh6

.. note::

   You can generate or obtain an already-generated API Key from
   https://bugzilla.mozilla.org/userprefs.cgi?tab=apikey.

.. important::

   Logging into MozReview will create a Bugzilla API Key named
   ``mozreview``. This API Key has limited permissions and isn't
   suitable for general use. It is recommended to create an API
   Key named ``mercurial`` or ``hg`` and define that in your Mercurial
   config.

IRC Nickname
^^^^^^^^^^^^

MozReview currently uses your IRC nickname as an identifier when
creating reviews. You will need to define it in your Mercurial
configuration file under the ``[mozilla]`` section.

Use the following as a template::

  [mozilla]
  ircnick = mynick

Configuring Review Repositories/Paths
=====================================

You almost certainly want to define the URL you will be pushing to in
your Mercurial configuration so you can type a short name (e.g.
``review``) rather than a full URL (which is longer and harder to
remember).

The sections below describe how to do this.

.. _mozreview_install_autoreview:

Configuring the Auto Review Repository
--------------------------------------

There is a special repository called the ``autoreview`` repository that
will automatically see what you are pushing and *redirect* your push to
the appropriate code review repository. In other words, you don't need
to configure a review path/remote for each clone: you simply define an
alias to the ``autoreview`` repository in your global Mercurial
configuration file and it should *just work*.

Using ``hg config -e -g`` to edit your global Mercurial configuration
file, add an entry under the ``[paths]`` section like so (be sure to use
the appropriate HTTP or SSH URL depending on what you have configured)::

   [paths]
   # For HTTP pushing
   review = https://reviewboard-hg.mozilla.org/autoreview

   # For SSH pushing
   review = ssh://reviewboard-hg.mozilla.org/autoreview

Now, you can ``hg push review`` from any Mercurial repository and it
will go to the ``autoreview`` repository and redirect to the appropriate
review repository automatically!

Advanced Paths Configuration
----------------------------

If the *auto review* repository is too much magic for you, you can
define the review URL for each repository you wish to review from.

.. important::

   We highly recommend the ``autoreview`` repository because it is much
   simpler to manage.

You will want to define a named path in your per-repository hgrc file.
We recommend the name ``review``. The URL for the repository is
``https://reviewboard-hg.mozilla.org/<repo>`` or
``ssh://reviewboard-hg.mozilla.org/<repo>`` (depending on whether you
are pushing over HTTP or SSH, respectively) where ``<repo>`` is
the name of a repository.

You can find the list of available repositories at
https://reviewboard-hg.mozilla.org/. For SSH URls, Just replace ``https://``
with ``ssh://``.

Edit your repository-local config via ``hg config -e`` and adjust your
``[paths]`` section to resemble something like::

  [paths]
  default = https://hg.mozilla.org/hgcustom/version-control-tools
  default-push = ssh://hg.mozilla.org/hgcustom/version-control-tools

  # For HTTP pushing
  review = https://reviewboard-hg.mozilla.org/version-control-tools

  # For SSH pushing
  review = ssh://reviewboard-hg.mozilla.org/version-control-tools
