.. _headless_repositories:

=====================
Headless Repositories
=====================

This document describes the architecture and state of Mozilla's headless
repositories.

History Lesson
==============

For the longest time, Mozilla operated a special Mercurial repository
called ``Try``. When people wanted to schedule a build or test job
against Firefox's release automation, they would create a special
Mercurial commit that contained metadata on what jobs to schedule. They
would push this commit (and its ancestors) to a new head on the ``Try``
repository. Firefox release automation would continuously poll the
repository via the pushlog data and would schedule jobs for new
pushes / heads according to the metadata in the special commit.

This approach was simple and worked for a long time without significant
issues. Unfortunately, Mercurial (and Git) have known scaling problems
as the number of repository heads approaches infinity. For Mozilla, we
start to encounter problems after a few thousand heads. Things started
to get really bad after 10,000 heads or so.

While fixing Mercurial to scale to thousands of heads would be
admirable, after talking with Mercurial core developers, it was apparent
that this would be a lot of work and the success rate was not considered
high, especially as we started talking about scaling to 1 million or
more heads. The recommended solution was to avoid the *mega-headed*
scaling problem alltogether and to limit ourselves to a bound number of
heads.

Headless Repositories
=====================

A headless repository is conceptually a single repository with thousands,
but with repository data stored outside the repository itself.

Clients still push to the repository as before. However, special code on
the server intercepts the incoming data and siphons it off to an
external store. A pointer to this external data is stored, allowing
the repository to serve up this data to clients that request it.

Mozilla plans to use headless repositories for Try and MozReview, which
share similar models of many clients writing to a central server with
limited, well-defined clients for that data.

Technical Details
-----------------

A Mercurial extension on the push server will intercept incoming changegroup
data and write a Mercurial bundle of that data to S3. This is tracked
in https://bugzilla.mozilla.org/show_bug.cgi?id=1078916.

A relational database will record information on each bundle - the URL,
what changesets it contains, etc. This database will be written to as
part of push by the aforementioned Mercurial extension. This is tracked
in https://bugzilla.mozilla.org/show_bug.cgi?id=1078920.

A Mercurial extension on the hgweb servers will serve requests for
S3-backend changesets. Clients accessing the server will be able to
request data in S3 as if it is hosted in the repository itself.
This is tracked in https://bugzilla.mozilla.org/show_bug.cgi?id=1078918.

The hgweb servers will also expose an HTTP+JSON API that matches the
existing pushlog API in order to allow clients to poll for new changes
without having to change their client-side code.

Initially, a one-off server to run the headless repositories will be
created. It will have one-off Mercurial versions, software stack, etc.
We may revisit server topology once things are rolled out and proved.
This is tracked in https://bugzilla.mozilla.org/show_bug.cgi?id=1057148.

Clients that pull Try data will need to either upgrade to Mercurial 3.2 or
install a custom extension that facilitates following links to S3 bundles.
This is because we plan to use Mercurial's bundle2 exchange format and
a feature we want to use is only available in Mercurial 3.2.

Low-Level Details
-----------------

1. Client performs `hg push ssh://hg.mozilla.org/try`
2. Mercurial queries remote and determines what missing changesets needs to
   be pushed.
3. Client streams changeset data to server.
4. Server applies public changesets to the repository and siphons draft
   changesets into a new bundle.
5. Public changesets are committed to the repository. Draft changesets
   are uploaded to S3 in a bundle file.
6. Server records metadata of S3-hosted files and push info into
   database.

