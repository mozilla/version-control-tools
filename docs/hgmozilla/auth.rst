.. _hgmozilla_auth:

==========================
Configuring Authentication
==========================

.. _auth_ssh:

SSH Configuration
=================

Pushing to Mercurial is performed via SSH. You will need to configure
your SSH client to talk appropriate settings to Mozilla's Mercurial
servers.

Typically, the only setting that needs configured is your username.
In your SSH config (likely ``~/.ssh/config``), add the following::

   Host hg.mozilla.org
     User me@mozilla.com

   Host reviewboard-hg.mozilla.org
     User me@mozilla.com

.. tip::
   Be sure to replace ``me@mozilla.com`` with your Mozilla-registered
   LDAP account that is configured for SSH access to Mercurial.

The first time you connect, you will be asked to verify the host SSH
key. The host key fingerprints are:

* hg.mozilla.org RSA: ``SHA256:usOyGXYDSaMWHhfvVeySzUD0yYxzmAvT+dVziygWsVQ.``

Verify your SSH settings are working by attempting to SSH into a server.
Your terminal output should resemble the following::

   $ ssh hg.mozilla.org
   A SSH connection has been successfully established.

   Your account (me@example.com) has privileges to access Mercurial over
   SSH.

   You did not specify a command to run on the server. This server only
   supports running specific commands. Since there is nothing to do, you
   are being disconnected.
   Connection to hg.mozilla.org closed.

Authenticating with Services
============================

Various Mercurial extensions interface with services such as Bugzilla.
In order to do so, they often need to send authentication credentials
as part of API requests. This document explains how this is done.

:py:mod:`mozhg.auth` contains a unified API for any Mercurial
extension or hook wishing to obtain authentication credentials.
New extensions are encouraged to use or add to this module instead
of rolling their own code.

.. _hgmozilla_finding_bugzilla_credentials:

Finding Bugzilla Credentials
============================

:py:meth:`mozhg.auth.getbugzillaauth` is the API used to request
credentials for ``bugzilla.mozilla.org``. It will attempt to find
credentials in the following locations:

1. The ``bugzilla.userid`` and ``bugzilla.cookie`` values from the
   active Mercurial config.
2. The ``bugzilla.username`` and ``bugzilla.password`` values from the
   active Mercurial config.
3. Login cookies from a Firefox profile.
4. Interactive prompting of username and password credentials.

Credential Extraction from Firefox Profiles
===========================================

As mentioned above, authentication credentials are searched for in
Firefox profiles. For example, Bugzilla login cookies are looked for
in Firefox's cookie database.

The first step of this is finding available Firefox profiles via the
current user's ``profiles.ini`` file.

By default, the available profiles are sorted. The default profile is
searched first. Remaining profiles are searched according to the
modification time of files in the profile - the more recent the
profile was used, the earlier it is searched.

If the ``bugzilla.firefoxprofile`` config option is present, it will
explicitly control the Firefox profile search order. If the value is a
string such as ``default``, only that profile will be considered.
If the value is a comma-delimited list, only the profiles listed will be
considered and profiles will be considered in the order listed.
