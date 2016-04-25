.. _mozreview_install:

=========================================
Configuring Your Machine to Use MozReview
=========================================

Configuring your machine to submit patches to MozReview requires the following
steps:

1. Obtain accounts and access privileges (those already active with Mozilla
   have likely already done this)
2. Configure your version control tool to connect with MozReview

Obtaining Accounts, Credentials, and Privileges
===============================================

To submit patches to MozReview, you will need:

* An active ``bugzilla.mozilla.org`` (BMO) account
* A BMO API Key

Those wishing to use advanced and more privileged features of MozReview will
need:

* A Mozilla LDAP account with Mercurial access and a registered SSH key

.. important::

   First time contributors don't require an LDAP account and can use most
   parts of MozReview with just a Bugzilla account.

A BMO account can be created at https://bugzilla.mozilla.org/createaccount.cgi.
(Instructions for creating BMO API Keys are described later.)

Instructions for obtaining a Mozilla LDAP account with Mercurial access
are documented at
`Becoming A Mozilla Contributor <https://www.mozilla.org/en-US/about/governance/policies/commit/>`_.

Benefits of Having an LDAP Account
----------------------------------

Having an LDAP account associated with MozReview grants the following
additional privileges:

* Ability to trigger *Try* jobs from MozReview
* Ability to land commits from the MozReview
* Reviews from people with level 3 will enable *Ship Its* (r+) to be
  carried forward.

.. important::

   Non-casual contributors are strongly encouraged to obtain and configure
   an LDAP account. This includes reviewers.

Updating SSH Config
-------------------

If you are using SSH to push to MozReview (requires an LDAP account), you will
want to configure your SSH username for ``reviewboard-hg.mozilla.org``.
See :ref:`auth_ssh` for instructions on updating your SSH client configuration,
including the SSH host key fingerprints.

.. tip::

   If you have already configured ``hg.mozilla.org`` in your SSH config,
   it is typically sufficient to copy the settings to
   ``reviewboard-hg.mozilla.org``.

.. _mozreview_install_ldap_associate:

Manually Associating Your LDAP Account with MozReview
=====================================================

If pushing to MozReview via HTTP (this includes all Git users) and you have
a Mozilla LDAP account, you will need to perform a one-time step to associate
your LDAP account with MozReview.

1. Ensure you have an account in MozReview by logging in at
   https://reviewboard.mozilla.org/
2. Execute the LDAP association command via SSH and follow the interactive
   wizard: ``$ ssh reviewboard-hg.mozilla.org mozreview-ldap-associate``

Successful association will resemble the following::

    $ ssh reviewboard-hg.mozilla.org mozreview-ldap-associate
    The following LDAP account will be associated with MozReview:

      me@example.com

    By SSHing into this machine, you have proved ownership of that
    LDAP account. We will need Bugzilla credentials to prove ownership
    of a Bugzilla account. These credentials are NOT stored on the
    server.

    Enter your Bugzilla e-mail address: me@example.com
    Enter a Bugzilla API Key: aslkhfr23rhl213j
    associating LDAP account me@example.com with Bugzilla account me@example.com...
    LDAP account successfully associated!
    exiting

.. tip::

   Your SSH username for ``reviewboard-hg.mozilla.org`` is your Mozilla LDAP
   username, which is an e-mail address. You may need to specify the
   ``-l`` argument to ``ssh`` to specify a username. e.g.
   ``ssh -l me@example.com reviewboard-hg.mozilla.org mozreview-ldap-associate``.

Configuring Your Version Control Client
=======================================

See :ref:`mozreview_install_mercurial` or :ref:`mozreview_install_git`.
