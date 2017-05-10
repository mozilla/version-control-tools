.. _vcssync_vendoring:

================================
Vendoring Projects in a Monorepo
================================

A monolithic repository (*monorepo*) is a version control repository
containing multiple projects and/or everything related to a project,
team, or company. Contrast with an approach where every logical unit
exists in its own repository.

While a monorepo may contain content for a project, that doesn't mean
that that project is canonically developed in that monorepo. For
example, the Firefox monorepo contains the source code for Servo
and WebRTC, but neither are canonically developed against
mozilla-central. Instead, commits to the canonical *upstream* repo
make their way to the monorepo through various means.

When it comes to vendoring projects in a monorepo, there are several
decisions that need to be made. This document attempts to describe
them.

Synchronization Frequency
=========================

If a project is canonically being developed outside the monorepo,
you'll need to decide how frequently upstream changes should be
incorporated in the monorepo.

The least structured approach is an *as needed* frequency. Essentially,
a human determines when a new version from upstream should be vendored
and then action is taken.

The other end of the spectrum is a 1:1 mapping: whenever a change is
made upstream, that change is essentially replayed in the monorepo.
This doesn't mean commits align exactly (you can squash commits together
for example). It does mean that every time a new *push* is made upstream
that something attempts to synchronize that change (if relevant) to
the monorepo.

Rewriting and Normalization
===========================

Monorepos like mozilla-central have standards for what commits
should look like. e.g. it favors linear history with commit-level
bisectability. And commit messages should be formatted in a certain
way.

Unless the monorepo and the upstream project share similar commit
authoring *style* conventions or the monorepo doesn't care about
consistency, it is likely that upstream commits will be rewritten
as part of vendoring in the monorepo. There are various rewriting
mechanisms that can be employed:

* Linearizing history to avoid merge commits
* Removing unwanted content from commit messages
* Prefixing commit message summary lines
* Adding annotations in commit message to denote upstream source
* Removing files or directories
* Renaming files or directories
* Running a transformation on file content
* Rewriting author/committer names and times

Each vendored project needs to decide what rewriting and normalization
to perform.

Trusting and Auditing Content
=============================

Any code or files have the potential to cause harm. For example:

* If a project's build system is invoked as part of building a
  common project in the monorepo, then from the perspective of that
  upstream project, you essentially have remote code execution
  privileges on the machines of developers relying on you.
* A project could relicense as GPLv3 (or similar liberal license),
  contaminating your code.
* A trademarked or patent protected file could be added, making
  you liable by extension.
* An attacker may target a vendored project because of lax code
  review standards in an attempt to attack something in your monorepo
  or its users.

Since every vendored project in a monorepo represents a point of
vulnerability, it is important that a trust relationship or expectation
be established. This especially holds true if content is being vendored
automatically in near real time. A risk analysis should be performed
and an auditing process should be established for all vendored content.

Initial Import
==============

Vendoring is a continuous endeavor. But before you get there, you
need to decide how the initial import should be performed.

The big decision that needs to be made is whether to do a bulk,
single commit import or whether to import with history. There
are pros and cons to each approach.

Single commit import pros:

* Simple to perform (just copy files)
* Minimal overhead for version control storage (no extra history to
  store)

History import pros:

* Code archeology over the imported project is simpler
* It's possible to bisect over history of the project
* The data will always be in the monorepo and can't disappear if the
  upstream project goes away
* Forces you to solve rewriting and normalization before any import
  is done and therefore helps identify mistakes and sub-optimal choices
  before they are a permanent part of history of the monorepo

Single commit import cons:

* Examining history of the imported project requires using a separate
  repo and/or tools
* No ability to bisect over history of imported project
* You run the risk of wanting project history in the monorepo later and
  not having it (this has happened a number of times in the Firefox
  monorepo, such as with mozharness)
* Data hosted for the *external* project may go away or be tampered with
  later

History import cons:

* Requires a lot of up-front work and verification
* Can introduce overhead to the repository (e.g. thousands of
  now-deleted files taking up megabytes of space)
* Can *pollute* history of the monorepo
* Can interfere with bisection operations against other projects
  in the monorepo

If a history import is performed, there is also the choice of how those
(possibly heavily rewritten) commits should be *joined* with the
history of the monorepo. The choices are between replaying the
commits onto an existing head or introducing a new *root* in the DAG
and merging it with an existing head.

The new *root* approach makes *bisect* more manageable by not
introducing a range of potentially thousands of commits in the middle
of the monorepo's history. In other words, when you naively bisect
every commit in the monorepo, you won't spend potentially several
iterations in the middle of the history of the imported project,
which has no relevant changes to the monorepo in the context of the
bisect operation.

The new *root* approach can also make some archeology operations
simpler and faster.

The main downside to the *root* approach is it is somewhat hacky.
Some tools can be confused by multiple DAG root nodes in a repository.
In practice, we don't think this is a huge issue. The history of the
Servo project vendored in the Firefox monorepo was added as a new root
node, for example.
