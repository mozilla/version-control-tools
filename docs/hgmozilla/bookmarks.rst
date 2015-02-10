.. _hgmozilla_bookmarks:

===============
Using Bookmarks
===============

The Mercurial project recommends the use of bookmarks for doing
development.

At its core, bookmarks are a labeling mechanism. Instead of a
numeric revision ID or alphanumeric SHA-1 (fragments), bookmarks
provide human-friendly identifiers to track and find changesets
or lines of work.

.. tip::

   If you are a Git user, bookmarks are similar to Git branches.
   Although they don't behave exactly the same.

Bookmarks and Feature Development
=================================

Bookmarks are commonly used to track the development of something -
a *feature* in version control parlance. The workflow is typically:

1. Create a bookmark to track a feature
2. Commit changes for that feature against that bookmark
3. Land the changes

Bookmarks typically exist from the time you start working on a feature
to the point that feature lands, at which time you delete the bookmark,
for it is no longer necessary.

Creating and Managing Bookmarks
===============================

Numerous guides exist for using bookmarks. We will not make an attempt
at reproducing their work here.

Recommending reading for using bookmarks includes:

* `The official Mercurial wiki <http://mercurial.selenic.com/wiki/Bookmarks>`_
* `Bookmarks Kick Start Guide <http://mercurial.aragost.com/kick-start/en/bookmarks/>`_
* `A Guide to Branching in Mercurial <http://stevelosh.com/blog/2009/08/a-guide-to-branching-in-mercurial/#branching-with-bookmarks>`_

The following sections will expand upon these guides.

Getting the Most out of Bookmarks
=================================

Use Mercurial 3.2 or Newer
--------------------------

Mercurial 3.2 adds notification messages when entering or leaving
bookmarks. These messages increase awareness for when bookmarks are
active.

Integrate the Active Bookmark into the Shell Prompt
---------------------------------------------------

If you find yourself forgetting which bookmark is active and you
want a constant reminder, consider printing the active bookmark as
part of your shell prompt. To do this, use the
`prompt extension <http://mercurial.selenic.com/wiki/PromptExtension>`_.

Understanding Head-Based Development
====================================

When you do feature development with bookmarks, you are committing
directly to the repository. When you create new bookmarks, you are
creating new heads in the repository.

To *create a head* means to add a new node to the directed acyclic
graph (DAG) such that its parent node now has multiple children. If
this doesn't make sense, please read
`this article <http://ericsink.com/entries/dvcs_dag_1.html>`_
about distributed version control systems and DAGs.

As soon as you have multiple heads in your repository, you need a
mechanism to interface with them.

The easiest way to see what heads exist in your repository is to run
``hg heads``::

  $ hg heads
  changeset:   4634:7847f747f167
  bookmark:    pushlog-rewrite
  user:        Gregory Szorc <gps@mozilla.com>
  date:        Tue Sep 09 12:43:48 2014 -0700
  summary:     Bug 1065050 - Rewrite pushlog as an extension

  changeset:   4647:4683fd9f9368
  bookmark:    pushlog-tests
  user:        Gregory Szorc <gps@mozilla.com>
  date:        Mon Sep 29 17:06:54 2014 -0700
  summary:     pushlog: add better tests for HTML output

  ...

Assuming you are using bookmarks and just want to find the list of
bookmarks, you may find the output of ``hg bookmarks`` more suitable::

  $ hg bookmarks
  fix-firefoxtree           4676:4a7444b8e597
  pushlog-rewrite           4634:7847f747f167
  pushlog-tests             4647:4683fd9f9368
  ...

.. note::

   Not all heads are bookmarks and not all bookmarks are heads.

   However, bookmarks tend to also be heads, so it is common to have
   overlap between the changesets identified by ``hg heads`` and ``hg
   bookmarks``.

A shortcoming of the output of both these commands is that you only see
a flat list of changesets. The real repository structure consists of a
DAG. When understanding how heads and bookmarks interact, it is very
useful to visualize this graph. For that, we have ``hg log --graph`` (or
``hg log -G`` to save some typing).::

  $ hg log -G
  o  changeset:   4647:4683fd9f9368
  |  parent:      4633:c3a9ed12ab3d
  |  bookmark:    pushlog-tests
  |  user:        Gregory Szorc <gps@mozilla.com>
  |  date:        Mon Sep 29 17:06:54 2014 -0700
  |  summary:     pushlog: add better tests for HTML output
  |
  | o  changeset:   4634:7847f747f167
  |/   bookmark:    pushlog-rewrite
  |    user:        Gregory Szorc <gps@mozilla.com>
  |    date:        Tue Sep 09 12:43:48 2014 -0700
  |    summary:     Bug 1065050 - Rewrite pushlog as an extension
  |
  o  changeset:   4633:c3a9ed12ab3d
  |  parent:      4631:83ee534dfb46
  |  user:        Gregory Szorc <gps@mozilla.com>
  |  date:        Thu Oct 23 17:51:14 2014 -0700
  |  summary:     hghooks: remove prevent_broken_csets hook (bug 1075275); r=glandium
  |
  o  changeset:   4631:83ee534dfb46
  |  user:        Gregory Szorc <gps@mozilla.com>
  |  date:        Wed Oct 29 22:21:58 2014 -0700
  |  summary:     docs: documenting advanced diff tool
  |
  o  changeset:   4630:c84facd720c6
  |  user:        Gregory Szorc <gps@mozilla.com>
  |  date:        Wed Oct 29 22:14:21 2014 -0700
  |  summary:     docs: more info on conducting reviews

From this view, we can clearly see the different heads - splitting -
in the DAG.

This command and view works great if all your heads are near the top of
the repository, your repository is small, and your repository doesn't
have a lot of splitting in the DAG. However, if any of those
conditions don't hold (as is often the case for real world
repositories), the output of the command quickly becomes too much to
easily comprehend.

The solution to this problem is to filter which changesets are deployed.
For that, we'll use a
`revision set <http://selenic.com/repo/hg/help/revsets>`_ (revset) to
limit output of ``hg log`` to changesets relevant to our
bookmarks/heads.

Let's start with a basic revset::

  $ hg log -G -r 'head()'
  o  changeset:   4839:11882cab05bd
  |  bookmark:    mozrepoman
  |  tag:         tip
  |  user:        Gregory Szorc <gps@mozilla.com>
  |  date:        Fri Nov 07 14:09:44 2014 -0800
  |  summary:     mozrepoman: add support for storing hgrc content in database
  |
  | @  changeset:   4836:b579bacb2f5c
  |/   bookmark:    docs
  |    parent:      4831:8306da26e997
  |    user:        Gregory Szorc <gps@mozilla.com>
  |    date:        Sat Nov 08 12:10:05 2014 -0800
  |    summary:     docs: INCOMPLETE bookmarks page
  |
  | o  changeset:   4779:2680be4b83b0
  |/   bookmark:    hgext-compat
  |    user:        Gregory Szorc <gps@mozilla.com>
  |    date:        Fri Nov 07 11:32:18 2014 -0800
  |    summary:     firefoxtree: mark as compatible with 3.2
  |
  | o  changeset:   4693:235ab29906a8
  |/   bookmark:    discovery-draft-hack
  |    parent:      4676:4a7444b8e597
  |    user:        Gregory Szorc <gps@mozilla.com>
  |    date:        Mon Nov 03 17:10:27 2014 -0800
  |    summary:     excludeheads: extension to exclude heads (bug 1093405)

This will show a graph view of all changesets that are a head.

When you run this command, you may notice something: the intermediary
commits between the head and the *branch point* of that head are
excluded. We need a way to show them too.

To achieve this, we'll use *phases*. Phases are Mercurial's way of
tracking which changesets have been shared - *published* in Mercurial
terms - with others. Changesets with a *public* phase have been
published with others. Changesets with a *draft* or *secret* phase
have not been published.

It we expand our query to exclude changesets in the public phase, we
have an approximate filter for *our ourstanding changesets.* We build
that revset::

  $ hg log -G -r 'head() or not public()'
  o  changeset:   4839:11882cab05bd
  |  bookmark:    mozrepoman
  |  tag:         tip
  |  user:        Gregory Szorc <gps@mozilla.com>
  |  date:        Fri Nov 07 14:09:44 2014 -0800
  |  summary:     mozrepoman: add support for storing hgrc content in database
  |
  o  changeset:   4838:0291e80cce96
  |  user:        Gregory Szorc <gps@mozilla.com>
  |  date:        Fri Nov 07 14:09:04 2014 -0800
  |  summary:     mozrepoman: establish project
  |
  o  changeset:   4837:2311ee205f90
  |  parent:      4831:8306da26e997
  |  user:        Gregory Szorc <gps@mozilla.com>
  |  date:        Tue Nov 04 11:39:43 2014 -0800
  |  summary:     checkstyle: extension to verify code style
  |
  | @  changeset:   4836:b579bacb2f5c
  |/   bookmark:    docs
  |    parent:      4831:8306da26e997
  |    user:        Gregory Szorc <gps@mozilla.com>
  |    date:        Sat Nov 08 12:10:05 2014 -0800
  |    summary:     docs: INCOMPLETE bookmarks page
  |
  | o  changeset:   4779:2680be4b83b0
  | |  bookmark:    hgext-compat
  | |  user:        Gregory Szorc <gps@mozilla.com>
  | |  date:        Fri Nov 07 11:32:18 2014 -0800
  | |  summary:     firefoxtree: mark as compatible with 3.2
  | |
  | o  changeset:   4778:b0a5081d4b24
  | |  user:        Gregory Szorc <gps@mozilla.com>
  | |  date:        Fri Nov 07 11:32:10 2014 -0800
  | |  summary:     bzpost: mark as compatible with 3.2
  | |
  | o  changeset:   4777:ba0c6efff456
  | |  user:        Gregory Szorc <gps@mozilla.com>
  | |  date:        Fri Nov 07 11:31:52 2014 -0800
  | |  summary:     bundleclone: mark as compatible with 3.2
  | |
  | o  changeset:   4776:b7c83b504d5d
  | |  parent:      4771:a928d04ea079
  | |  user:        Gregory Szorc <gps@mozilla.com>
  | |  date:        Fri Nov 07 12:06:00 2014 -0800
  | |  summary:     testing: test with Mercurial 3.2 by default
  | |
  | o  changeset:   4771:a928d04ea079
  | |  parent:      4766:b94c32c4a44b
  | |  user:        Gregory Szorc <gps@mozilla.com>
  | |  date:        Fri Nov 07 11:31:25 2014 -0800
  | |  summary:     testing: update Mercurial versions to reflect release of 3.2 (bug 1095676)
  | |
  | o  changeset:   4766:b94c32c4a44b
  |/   parent:      4742:4f8f083f7f0c
  |    user:        Gregory Szorc <gps@mozilla.com>
  |    date:        Fri Nov 07 11:59:41 2014 -0800
  |    summary:     reviewboard: suppress output from hg up
  |
  | o  changeset:   4693:235ab29906a8
  |/   bookmark:    discovery-draft-hack
  |    parent:      4676:4a7444b8e597
  |    user:        Gregory Szorc <gps@mozilla.com>
  |    date:        Mon Nov 03 17:10:27 2014 -0800
  |    summary:     excludeheads: extension to exclude heads (bug 1093405)

Note the addition of ``4838:0291e80cce96`` and ``4837:2311ee205f90`` on the
tip-most head. These are the ancestor commits in the ``mozext`` bookmark
head. These are not yet public, so they were pulled in from the revset.

This revset clearly shows us our local, unpublished changes. But we
still don't have an important part of the graph: the parent changeset.
It looks like all these heads are next to each other in the DAG.

We make the output slightly more usable by adding in the parent of the
commits::

  $ hg log -G -r 'head() or not public() or parents(not public())'
  o  changeset:   4839:11882cab05bd
  |  bookmark:    mozrepoman
  |  tag:         tip
  |  user:        Gregory Szorc <gps@mozilla.com>
  |  date:        Fri Nov 07 14:09:44 2014 -0800
  |  summary:     mozrepoman: add support for storing hgrc content in database
  |
  o  changeset:   4838:0291e80cce96
  |  user:        Gregory Szorc <gps@mozilla.com>
  |  date:        Fri Nov 07 14:09:04 2014 -0800
  |  summary:     mozrepoman: establish project
  |
  o  changeset:   4837:2311ee205f90
  |  parent:      4831:8306da26e997
  |  user:        Gregory Szorc <gps@mozilla.com>
  |  date:        Tue Nov 04 11:39:43 2014 -0800
  |  summary:     checkstyle: extension to verify code style
  |
  | @  changeset:   4836:b579bacb2f5c
  |/   bookmark:    docs
  |    parent:      4831:8306da26e997
  |    user:        Gregory Szorc <gps@mozilla.com>
  |    date:        Sat Nov 08 12:10:05 2014 -0800
  |    summary:     docs: INCOMPLETE bookmarks page
  |
  o  changeset:   4831:8306da26e997
  |  bookmark:    @
  |  user:        Gregory Szorc <gps@mozilla.com>
  |  date:        Sat Nov 08 12:30:23 2014 -0800
  |  summary:     mozext: mark as compatible with Mercurial 3.2
  |
  |
  | o  changeset:   4779:2680be4b83b0
  | |  bookmark:    hgext-compat
  | |  user:        Gregory Szorc <gps@mozilla.com>
  | |  date:        Fri Nov 07 11:32:18 2014 -0800
  | |  summary:     firefoxtree: mark as compatible with 3.2
  | |
  | o  changeset:   4778:b0a5081d4b24
  | |  user:        Gregory Szorc <gps@mozilla.com>
  | |  date:        Fri Nov 07 11:32:10 2014 -0800
  | |  summary:     bzpost: mark as compatible with 3.2
  | |
  | o  changeset:   4777:ba0c6efff456
  | |  user:        Gregory Szorc <gps@mozilla.com>
  | |  date:        Fri Nov 07 11:31:52 2014 -0800
  | |  summary:     bundleclone: mark as compatible with 3.2
  | |
  | o  changeset:   4776:b7c83b504d5d
  | |  parent:      4771:a928d04ea079
  | |  user:        Gregory Szorc <gps@mozilla.com>
  | |  date:        Fri Nov 07 12:06:00 2014 -0800
  | |  summary:     testing: test with Mercurial 3.2 by default
  | |
  | o  changeset:   4771:a928d04ea079
  | |  parent:      4766:b94c32c4a44b
  | |  user:        Gregory Szorc <gps@mozilla.com>
  | |  date:        Fri Nov 07 11:31:25 2014 -0800
  | |  summary:     testing: update Mercurial versions to reflect release of 3.2 (bug 1095676)
  | |
  | o  changeset:   4766:b94c32c4a44b
  |/   parent:      4742:4f8f083f7f0c
  |    user:        Gregory Szorc <gps@mozilla.com>
  |    date:        Fri Nov 07 11:59:41 2014 -0800
  |    summary:     reviewboard: suppress output from hg up
  |
  o  changeset:   4742:4f8f083f7f0c
  |  parent:      4739:4056a46cb4af
  |  user:        Francois Marier <francois@mozilla.com>
  |  date:        Thu Nov 06 18:40:36 2014 +1300
  |  summary:     Bug 1094597 - Fix typo in the manual; r=gps
  |
  | o  changeset:   4693:235ab29906a8
  |/   bookmark:    discovery-draft-hack
  |    parent:      4676:4a7444b8e597
  |    user:        Gregory Szorc <gps@mozilla.com>
  |    date:        Mon Nov 03 17:10:27 2014 -0800
  |    summary:     excludeheads: extension to exclude heads (bug 1093405)
  |
  o  changeset:   4676:4a7444b8e597
  |  bookmark:    fix-firefoxtree
  |  user:        Gregory Szorc <gps@mozilla.com>
  |  date:        Sun Oct 19 21:17:54 2014 -0700
  |  summary:     firefoxtree: prevent unknown reference to _updateremoterefs (bug 1085066)

We see some new entries, such as ``4831:8306da26e997``. These allow us
to see exactly what the base commit of each head is - something very
useful when you want to rebase changesets.

Using the revset ``head() or not public() or parents(not public())``
along with ``hg log -G`` provides a mechanism to identify changesets on
feature bookmarks that haven't been published yet. (Technically it
identifies changesets on heads without bookmarks as well.) Quickly
sorting out the state of your heads and bookmarks is essential for
head/bookmark-based development.

.. tip::

   If you would like to further customize the output and functionality
   of the above command, we recommend following the instructions at
   `Customizing Mercurial Like a Pro <http://jordi.inversethought.com/blog/customising-mercurial-like-a-pro/>`_.

   That page will minify the output, add color, and create a command
   alias so the output is easier to understand and closer to your
   fingertips.

Collaborating / Sharing Bookmarks
=================================

Say you have multiple machines and you wish to keep your bookmarks in
sync across all of them. Or, say you want to publish a bookmark
somewhere for others to pull from. For these use cases, you'll need a
server accessible to all parties to push and pull from.

If you have Mozilla commit access, you can
`create a user repository <https://developer.mozilla.org/en-US/docs/Creating_Mercurial_User_Repositories>`_
to hold your bookmarks.

If you don't have Mozilla commit access or don't want to use a user
repository, you can create a repository on Bitbucket.

If neither of these options work for you, you can always run your own
Mercurial server.

Pushing and Pulling Bookmarks
-----------------------------

``hg push`` by default won't transfer bookmark updates. Instead, you
need to use the ``-B`` argument to tell Mercurial to push a bookmark
update. e.g.::

   $ hg push -B my-bookmark user
   pushing to user
   searching for changes
   remote: adding changesets
   remote: adding manifests
   remote: adding file changes
   remote: added 1 changesets with 1 changes to 1 files
   exporting bookmark my-bookmark

.. tip::

   When pushing bookmarks, it is sufficient to use ``-B`` instead of
   ``-r``.

   When using ``hg push``, it is a common practice to specify ``-r
   <rev>`` to indicate which local changes you wish to push to the
   remote. When pushing bookmarks, ``-B <bookmark>`` implies
   ``-r <bookmark>``, so you don't need to specify ``-r <rev>``.

Unlike ``hg push``, ``hg pull`` will pull all bookmark updates
automatically. If a bookmark has been added or updated since the last
time you pulled, ``hg pull`` will tell you so. e.g.::

   $ hg pull user
   pulling from user
   pulling from $TESTTMP/a (glob)
   searching for changes
   adding changesets
   adding manifests
   adding file changes
   added 1 changesets with 1 changes to 1 files (+1 heads)
   updating bookmark my-bookmark

Things to Watch Out For
-----------------------

Mercurial repositories are publishing by default. If you push to a
publishing repository, your Mercurial client won't let you modify
pushed changesets.

As of February 2015, user repository on hg.mozilla.org are
non-publishing by default, so you don't have to worry about this.
However, if you use a 3rd party hosting service, this could be
a problem. Some providers have an option to mark repositories as
non-publishing. This includes Bitbucket. **If you plan on sharing
bookmarks and rewriting history, be sure you are using a non-publishing
repository.**

Relationship to MQ
==================

Many Mercurial users (especially at Mozilla) may be familiar with MQ.
MQ is a workflow extension in Mercurial that allows users to take a
patch-centric approach to feature development. This approach is
contrasted with a bookmark workflow's head-based approach.

.. important::

   The Mercurial project recommends bookmark workflows for new Mercurial
   users. Use of MQ is somewhat discouraged by Mercurial project
   contributors.

Head-based workflows (read: using bookmarks) are better integrated into
Mercurial's core workflows. For example, when you run ``hg rebase``
to move your feature commits in the DAG (say as part of landing),
Mercurial has the proper context to perform a 3-way merge and Mercurial
will invoke the merge tool, if necessary. Contrast with MQ, which will
produce ``.rej`` files. Merge tools are much more usable.

Head-based workflows also enable the use of ``hg histedit``. This
command allows you to perform complex history rewriting with a single
command invocation (much like ``git rebase -i``). To perform the
equivalent in MQ would require several commands.

Head-based workflows are also more compatible with
:ref:`MozReview <mozreview>`, Mozilla's code review tool.

MQ is also not compatible with
`Changeset Evolution <http://mercurial.selenic.com/wiki/ChangesetEvolution>`_,
Mercurial's mechanism for better handling history rewriting.

.. important::

   We highly recommend Mozillians **avoid MQ** and use head-based
   development (via bookmarks) instead.
