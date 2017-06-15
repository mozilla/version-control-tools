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
key.

The fingerprints of the host keys for ``hg.mozilla.org`` are as follows:

.. code::

   ED25519 (server preferred key)
   256 SHA256:7MBAdqLe8+aSYkv+5/2LUUxd+WdgYcVSV+ZQVEKA7jA hg.mozilla.org
   256 SHA1:Ft++OU96cvaREKNFCJ6AiuCpGac hg.mozilla.org
   256 MD5:96:eb:3b:78:f5:ca:19:e2:0c:a0:95:ea:04:28:7d:26 hg.mozilla.org

   RSA
   4096 SHA256:RX2OK8A1KNWdxyu6ibIPeEGLBzc5vyQW/wd7RKjBehc hg.mozilla.org
   4096 SHA1:p2MGe4wSw8ZnQ5J9ShBk/6VA+Co hg.mozilla.org
   4096 MD5:1c:f9:cf:76:de:b8:46:d6:5a:a3:00:8d:3b:0c:53:77 hg.mozilla.org

And for ``reviewboard-hg.mozilla.org``:

.. code::

   ED25519 (server preferred key)
   256 SHA256:4zGDMk+ftX6ZmYX5A25HxqbtujOvv+MQGj99u931dwA reviewboard-hg.mozilla.org
   256 SHA1:5K5e1UWQluIlbgsTDBUwY5k4Xqk reviewboard-hg.mozilla.org
   256 MD5:0b:4c:0d:7e:3e:79:5a:6a:c9:bb:a2:3f:5d:d8:83:d9 reviewboard-hg.mozilla.org

   RSA
   SHA256:O6C9zLi4leD/mb4lPNmR50R1ampZgeEi7StDEbZDmyA
   MD5:a6:13:ae:35:2c:20:2b:8d:f4:8d:8e:d7:a8:55:67:97

A GPG signed document stating asserting the validity of these keys can
be verified:

.. code-block:: bash

   curl https://hg.mozilla.org/hgcustom/version-control-tools/raw-file/tip/docs/vcs-server-info.asc > mozilla-vcs-info.asc
   gpg --verify mozilla-vcs-info.asc

Verify your SSH settings are working by attempting to SSH into a server.
Your terminal output should resemble the following::

   $ ssh hg.mozilla.org
   A SSH connection has been successfully established.

   Your account (me@example.com) has privileges to access Mercurial over
   SSH.

  You are a member of the following LDAP groups that govern source control
  access:

     scm_level_1

  This will give you write access to the following repos:

     Try

  You will NOT have write access to the following repos:

     Autoland (integration/autoland), Firefox Repos (mozilla-central, releases/*), ...

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
