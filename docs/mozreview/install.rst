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

.. important::

   Non-casual contributors are strongly encouraged to obtain and configure
   an LDAP account.

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

Configuring Your Version Control Client
=======================================

See :ref:`mozreview_install_mercurial`.
