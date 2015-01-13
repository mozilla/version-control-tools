.. _hgmozilla_auth:

============================
Authentication with Services
============================

Various Mercurial extensions interface with services such as Bugzilla.
In order to do so, they often need to send authentication credentials
as part of API requests. This document explains how this is done.

:py:mod:`mozhg.auth` contains a unified API for any Mercurial
extension or hook wishing to obtain authentication credentials.
New extensions are encouraged to use or add to this module instead
of rolling their own code.

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
current user's ``profiles.ini`` file. Next, the available profiles are
sorted. The default profile is searched first. Remaining profiles are
searched according to the modification time of files in the profile -
the more recently the profile was used, the earlier it is searched.
