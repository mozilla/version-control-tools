.. _hgmo_firefoxreleases:

====================
Firefox Release Data
====================

hg.mozilla.org has facilities for aggregating and exposing information about
Firefox releases performed from Mercurial changesets.

.. important::

   This feature is currently experimental and implementation details may
   change. If you would like the feature to stabilize, please ping *gps*
   in ``#vcs`` on irc.mozilla.org.

This feature is currently only enabled on the
`mozilla-central <https://hg.mozilla.org/mozilla-central>`_ repository.

Features
========

Release Info on Changeset Pages
-------------------------------

Changeset pages like https://hg.mozilla.org/mozilla-central/rev/1362c0928dc1
display information on Firefox releases in relation to that changeset.

Most pages should have a *first release with* and *last release without*
section. Exceptions include changesets in the very early and very modern
repository history. (This info isn't displayed unless we can find a release
in both directions.)

If a release was made from that changeset, there will also
be information on those releases. e.g.
https://hg.mozilla.org/mozilla-central/rev/09a4282d1172. This includes a
link to the pushlog containing changesets landed between two releases.

Listing of Known Releases
-------------------------

The ``firefoxreleases`` web command renders known Firefox releases from
changesets in a repo. e.g.
https://hg.mozilla.org/mozilla-central/firefoxreleases.

A JSON view is available by using the ``json-firefoxreleases`` web command.
e.g. https://hg.mozilla.org/mozilla-central/json-firefoxreleases.

Filtering by *platform* is available by specifying the ``platform`` query
string argument. e.g.
https://hg.mozilla.org/mozilla-central/firefoxreleases?platform=win32.

.. note::

   If you want to read this data from machines, a better source might be
   https://mozilla-services.github.io/buildhub/.