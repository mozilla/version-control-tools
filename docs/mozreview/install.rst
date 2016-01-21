.. _mozreview_install:

=========================================
Configuring Your Machine to Use MozReview
=========================================

Obtaining Accounts, Credentials, and Privileges
===============================================

Pushing to MozReview to **initiate** code review requires the following:

* An active ``bugzilla.mozilla.org`` (BMO) account
* A BMO API Key
* (optional) A Mozilla LDAP account with Mercurial access and a
  registered SSH key

A BMO account can be created at https://bugzilla.mozilla.org/createaccount.cgi.

Once you have an account, visit
https://bugzilla.mozilla.org/userprefs.cgi?tab=apikey to generate a new
API Key. The API Key can have any description you want. We recommend
something like ``mercurial`` or ``git``. The API Key won't be used until
later, so you don't have to generate it right away.

Instructions for obtaining a Mozilla LDAP account with Mercurial access
are documented at
`Becoming A Mozilla Contributor <https://www.mozilla.org/en-US/about/governance/policies/commit/>`_.

LDAP/SSH Versus HTTP
====================

Reviews are initiated with MozReview by pushing to a Mercurial *review*
repository. Pushing via both SSH and HTTP are supported.

Pushing via HTTP is the easiest to configure **and is recommended for
new contributors**. All you need to push via HTTP is an active Bugzilla
account and Bugzilla API Key.

Pushing via SSH requires a Mozilla LDAP account configured with
Mercurial access and with a registered SSH key. This involves a little
more time and work to obtain. **This is recommended for Mozilla staff and
beyond-casual contributors.**

.. important::

   Pushing via SSH grants additional privileges in the MozReview web
   interface, such as the ability to trigger *Try* jobs and interact
   with the *Autoland* code landing service. If you push things via HTTP
   and have never pushed via SSH before, you will need someone else to
   trigger *Try* jobs for you.

Updating SSH Config
-------------------

If you are using SSH to push to MozReview, you will want to configure your
SSH username for ``reviewboard-hg.mozilla.org``. See :ref:`auth_ssh` for
instructions on updating your SSH client configuration, including the SSH host
key fingerprints.

.. tip::

   If you have already configured ``hg.mozilla.org`` in your SSH config,
   it is typically sufficient to copy the settings to
   ``reviewboard-hg.mozilla.org``.

Configuring Your Version Control Client
=======================================

See :ref:`mozreview_install_mercurial`.
