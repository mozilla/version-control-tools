.. _hgmo_apis:

===========
Custom APIs
===========

In addition to the APIs and services that Mercurial provides out-of-the-box,
hg.mozilla.org offers a handful of custom APIs for services to
consume.

Pushlog
=======

The Pushlog records when pushes are made to a repository and who made
them. See :ref:`pushlog` for more.

Firefox Releases
================

Firefox repositories are able to expose information about the set
of Firefox releases tied to Mercurial changesets in that repository.
See :ref:`hgmo_firefoxreleases` for more.

Repository Metadata
===================

The ``repoinfo`` web command provides additional information about
a repository, such as the group membership required to push to that
repository.

See e.g. https://hg.mozilla.org/mozilla-central/repoinfo and
https://hg.mozilla.org/mozilla-central/json-repoinfo.

Automation Relevance
====================

The ``automationrelevance`` web command provides information on
what changesets are *relevant* to automated consumers given a source
changeset.

URLs have the form ``<repo>/json-automationrelevance/<changeset>``.
e.g. https://hg.mozilla.org/integration/autoland/json-automationrelevance/67342f5762dd6e7ea3a783876cd9d35517ff3386.

The data contains a set of changesets and corresponding metadata
(such as pushlog info and the set of files changed). The *relevant*
changesets are the changesets that should be used to influence
scheduling of tasks that examine the correctness of those changesets.

For most repositories, the *relevant* set consists of changesets
in the same push as the queried changeset.

For special repositories (notably the *try* repositories), the
*relevant* set is supplemented by non-public ancestors of the queried
changeset. e.g. if you push a series of changesets to Try and then
iterate on just the last changeset, the *relevant* set on subsequent
pushes will include the base changesets from previous push(es).
