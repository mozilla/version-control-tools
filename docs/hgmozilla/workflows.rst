.. _hgmozilla_workflows:

=========
Workflows
=========

Mercurial is a flexible tool that allows you to choose from several
workflows and variations thereof.

.. important::

   Before reading on, it is important to have a firm grasp on the
   concepts described in :ref:`hgmozilla_dag`. That article describes
   how Mercurial models repository history as a directional acyclic
   graph (DAG) and understanding of this is critical for many
   workflows.

Feature Branches and Head-Based Development
===========================================

As mentioned in :ref:`hgmozilla_dag`, DAG branches are commonly used
to work on isolated units of change. DAG branches used this way are
called *feature branches* because each DAG branch tracks a specific
*feature* or line of work.

Another way to think about this is as *head-based development*. Each
DAG branch has its own head node (this is a basic property of directed
acyclic graphs). So, working on different DAG branches is effectively
working on different heads.

The general way feature branches/head-based development work is:

1. Set your starting point via ``hg up <starting node>``.
2. Modify files
3. ``hg commit``
4. Repeat #2 and #3 until work is done
5. Integrate DAG branch somehow (typically a rebase or merge)

To help understand this, let's start with the following state::

   $ hg log -G -T '{node|short} {desc}'
   @  2bf9b23b2d03 D
   |
   o  0f165760af41 C
   |
   o  7175417717e8 B
   |
   o  8febb2b7339e A

The working directory is based on ``D``. But we don't like the state
of ``D``, so we decide to start working from ``B`` instead::

   $ hg up 7175417717e8
   $ echo changes > file
   $ hg commit -m E
   created new head
   $ echo 'more changes' > file
   $ hg commit -m F

You get bored working on that feature. Or, you run into some obstacles
and want to try a fresh approach. So, you decide to start a new
*feature branch*::

   $ hg up 7175417717e8
   $ echo 'new feature' > file
   $ hg commit -m G
   $ echo 'more new features' > file
   $ hg commit -m H

Then you have a revelation about the first feature branch you were
working on and go back to make a change::

   $ hg up 82123e512a06
   $ echo revelation > file
   $ hg commit -m I

Our repository now looks like::

   $ hg log -G -T '{node|short} {desc}'
   @  bcb7c3592ba2 I
   |
   | o  2ca760d1e4fe H
   | |
   | o  d6248a455a1b G
   | |
   o |  82123e512a06 F
   | |
   o |  bed01724d682 E
   |/
   | o  2bf9b23b2d03 D
   | |
   | o  0f165760af41 C
   |/
   o  7175417717e8 B
   |
   o  8febb2b7339e A

To the uninitiated, this view can look complicated because it kind of
is. You've got a number of commits and lines going every which way.
And, you can imagine how complicated things can become if you are
working on several heads and/or the repository history is large and/or
fast moving. We need tools beyond ``hg log -G`` to help us sort through
these commits.

Finding Heads
=============

The ``hg heads`` command can be used to quickly see all repository heads.
Running it on our current repository will reveal something like::

   $ hg heads
   changeset:   8:bcb7c3592ba2
   tag:         tip
   parent:      5:82123e512a06
   user:        Gregory Szorc <gps@mozilla.com>
   date:        Wed Aug 12 12:57:28 2015 -0700
   summary:     I

   changeset:   7:2ca760d1e4fe
   user:        Gregory Szorc <gps@mozilla.com>
   date:        Wed Aug 12 12:52:26 2015 -0700
   summary:     H

   changeset:   3:2bf9b23b2d03
   user:        Gregory Szorc <gps@mozilla.com>
   date:        Wed Aug 12 11:57:08 2015 -0700
   summary:     D

.. tip::

   ``hg heads`` is roughly equivalent to ``hg log -r 'head()'``, which
   uses the ``head()`` revision set function to only select head
   changesets/nodes.

``hg heads`` can be useful to get a quick overview of all *unmerged*
DAG branches. If the canonical repository only has a single head, then
``hg heads`` will be a good approximation for *what work hasn't been
merged yet*. But if the canonical repository has many heads (this is
frequently the case), then ``hg heads`` may lose some of its utility
because it will display **all** heads, not just the ones you care about.

Read on for some ways to deal with this.

Labeling
========

Up until this point, all our Mercurial commands were interacting with
the 12 character hex abbreviation of the full SHA-1 changeset. These
values are effectively random, opaque, and difficult to memorize. It
can be annoying and possibly difficult for humans to grasp with
them. This is why Mercurial provides facilitites for *labeling*
heads and changesets. There are many forms of labels in Mercurial.

Bookmarks
---------

Bookmarks are specially behaving labels attached to changesets.
When you commit when a bookmark is *active*, the active
label/bookmark automatically moves to the just-committed changeset.

For more on bookmarks, see :ref:`hgmozilla_bookmarks`.

Bookmarks users may find the ``hg bookmarks`` command useful,
as it prints a concise summary of all bookmarks. This is arguably
a better version of ``hg heads``, which we learned about above.
However, a downside of ``hg bookmarks`` is that it only shows the
changesets with bookmarks: it doesn't show other changesets in
that head or the overall DAG. For that, we'll need more powerful
tools. Keep reading to learn more.

Branches
--------

Mercurial branches (not to be confused with generic *DAG branches*)
are a more heavyweight label that can be applies to changesets.
Unlike bookmarks whose labels move as changesets are committed,
branches are stored inside the changeset itself and are permanent.

When you make a Mercurial branch active, all subsequent commits
will forever be associated with that branch.

Branches are useful for long-running heads, such as tracking releases.
However, their utility for short-lived feature development is
widely considered to be marginal. And for large repositories, the
presence of hundreds or even thousands of branches over time or
from hundreds of developers can lead to a lot of clutter and
confusion.

.. important::

   The use of Mercurial branches for feature development is highly
   discouraged. For Firefox, Mercurial branches are never used
   for tracking features.

Because the use of Mercurial branches is discouraged, we won't
describe how they are used.

MQ
==

Mercurial Queues (MQ) is a workflow extension that focuses on
interacting with stacks of labeled patches. Contrast this with
head-based workflows, where you are interacting with nodes and
heads on the repository DAG.

Some like MQ because it hides the complexity of the DAG. It takes
a simple and easily comprehended approach to working on things.
However, it also has numerous setbacks:

* MQ doesn't perform 3-way merges and thus merge conflicts (in the
  form of *.rej* files) are much more common.
* Managing labels for every single changeset can be cumbersome,
  introducing overhead that encourages fewer, larger, and
  harder-to-review commits.
* Performance on large repositories can be horrible.
* The extension isn't actively developed and bugs often go unfixed.
* MQ doesn't work as well with :ref:`MozReview <mozreview>` as
  head-based workflows.

.. important::

   The Mercurial project doesn't recommend MQ, especially for new
   Mercurial users. At Mozilla, we also recommend not using MQ.
   Use a head-based workflow instead.

Refining What Changesets are Shown
==================================

``hg heads``, ``hg bookmarks``, ``hg branches``, ``hg qseries``,
and other commands meant to summarize common entities within the
repository each suffer from the limitation that they often show
too little information. When doing development, you often want
to see all the changesets in a head or want to see the shape of
the DAG. We need a way to view the important information from
the aforementioned commands, without the overload that ``hg log -G``
gives us. Fortunately, Mercurial has an answer.

The output from the ``hg log`` command can be highly configurable
via the use of *revision sets (revsets)* and *templates*. The former
determines what to show and the latter how to show it.

When we run ``hg log -G``, Mercurial will display information for
**all** changesets and render it according to the default command
line template. As you'll quickly learn, this is far from an ideal
way to find changesets you care about.

For a fast and information rich display of changesets relevant to
you - a view on the heads/features you've been working on - we
highly recommend the ``hg wip`` command described at
`Customizing Mercurial Like a Pro <http://jordi.inversethought.com/blog/customising-mercurial-like-a-pro/>`_.

To Label or Not to Label
========================

Before we learned about bookmarks, branches, and MQ patches, we
learned how to create label-less DAG branches. Various Mercurial
workflows use labels because they are more human friendly than
SHA-1 fragments. But, they aren't required.

.. note::

   The concept of label-less heads does not exist in Git: Git
   requires all heads to have a label (a Git branch name) or the
   head and the commits unique to it will eventually be deleted
   via garbage collection.

   Because Git requires labels and Mercurial does not, it is
   accurate to say that Mercurial has lighter weight DAG branches
   than Git!

Since Mercurial doesn't require labels, it raises an interesting
question: should you use labels?

The answer, like most things, depends.

Custom and powerful query and rendering tools like the
aforementioned ``hg wip`` command are sufficient for many to simply
not need labels and to use anonymous, unlabeled changesets and heads
for everything. A benefit to this approach is less overhead
interacting with and managing labels: you don't need to make
a bookmark or branch active: you just update to a changeset, make
changes, and commit. You don't need to clean up labels when you
are done. It's all very low-level and feels fast. It also contributes
to understanding of the DAG and its concepts.

A downside of label-less workflows is you have to interact with
SHA-1s or SHA-1 fragments all the time. There is a lot of copying
and pasting of these values in order to run commands. And, this
is simply too much for some people. Some just need human-friendly
labels.
