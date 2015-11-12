.. _hgmozilla_dag:

=====================
The DAG and Mercurial
=====================

Distributed version control systems (DVCS) like Mercurial (and Git)
utilize a directed acyclic graph (DAG) for representing commits. This
DAG is how the *history* of a repository is stored and often
represented.

To help understand how this works, we'll be using Mercurial commands
to show and manipulate the DAG.

We start by creating an empty Mercurial repository with an empty
graph::

   $ hg init repo
   $ cd repo

The Mercurial command for inspecting the repository history (and the
DAG by extension) is ``hg log``. Let's run it on our empty repository::

   $ hg log -G

No output. This is confirmation that the graph is empty.

.. note::

   We use ``-G`` throughout this article because it is necessary to
   print a visual representation of the DAG.

Adding Nodes
============

We'll need to create nodes to make our DAG interesting. The way we do
this is by *committing*. But first, we need something to commit. Let's
create a file::

   $ echo 1 > file

Then we tell Mercurial that we're interested in storing the history of
this file::

   $ hg add file

We then use ``hg commit`` to create a new node (*changeset* in Mercurial
parlance) and add it to the DAG::

   $ hg commit -m A

(``-m A`` says to use ``A`` for the commit message.

Now let's take a look a the DAG::

   $ hg log -G -T '{desc}'
   @  A

.. note::

   ``-T '{desc}'`` tells Mercurial to only print the *description* or
   *commit message* from the changeset/node. Without it, output would be
   much more verbose.

It looks like we have a single node - denoted by ``@`` and ``A``.

This graph / repository state isn't very interesting. So, we perform
another commit::

   $ echo 2 >> file
   $ hg commit -m B

And then inspect the DAG::

   $ hg log -G -T '{desc}'
   @  B
   |
   o  A

This is slightly more interesting!

The ``B`` node has been introduced. That is pretty obvious.

``A`` has its node represented by a ``o``. ``B`` has its node represented
by ``@``. Mercurial uses ``@`` to represent the node currently attached
to the *working directory*. This will be discussed later.

The first column has grown a vertical pipe character (``|``) between
the two entries. In graph terms, this is an *edge*. While the visualization
doesn't indicate it, ``B`` internally stores a pointer back to ``A``.
This constitutes the *edge* and since the edge is directional
(``B`` to ``A``), that makes the graph *directed* (the *D* from
*DAG*).

Directed graphs borrow terminology from biology to represent
relationships between nodes:

parent node
   A node that came before another (is referred to by another node).
child node
   A node that derives directly from another.
root node
   A node that has no parents.
head node
   A node that has no children.
descendants
   All the children, the children's children, the children's children's
   children, and so on of a node.
ancestors
   The parents, parents' parents, parents' parents' parents, and so
   on of a node.

In our graph so far:

* ``A`` is the parent of ``B``
* ``B`` is a child of ``A``
* ``A`` is a root
* ``B`` is a head
* The descendants of ``A`` are just ``B``.
* The ancestors of ``B`` are just ``A``.

If you don't understand this, let's try committing a few more nodes
to help your understanding.::

   $ echo 3 >> file
   $ hg commit -m C
   $ echo 4 >> file
   $ hg commit -m D

   $ hg log -G -T '{desc}'
   @ D
   |
   o C
   |
   o B
   |
   o A

``A`` is still the root node. Since ``B`` has children, it is no
longer a *head*. Instead, ``D`` is now our head node.

If all you do is ``hg commit`` like we've been doing so far, your
repository's DAG will be a linear chain of nodes, just like we
have constructed above. 1 head. Every node has 1 parent (except the
root).

.. important::

   The important takeaway from this section is that the *history*
   of Mercurial repositories is stored as a DAG. ``hg commit``
   creates a changeset and appends a node to a graph. A DAG node
   and a Mercurial changeset are effectively the same thing.

Nodes are Hashes of Content
===========================

Up to this point, we've been using our single letter commit messages
(``A``, ``B``, etc) to represent nodes in our DAG. This is good
for human understanding, but it hides an important detail of how
Mercurial actually works.

Mercurial uses a SHA-1 digest to identify each node/changeset in the
repository/DAG. The SHA-1 digest is obtained by hashing the content
of the changeset.

Essentially, Mercurial changesets consist of various pieces of data
including but not limited to:

1. The parent node(s)
2. The set of files and their state
3. The author
4. The date
5. The commit message

Mercurial assembles all these pieces of data in a well-defined manner,
feeds the result into a SHA-1 hasher, and uses the digest of the result
as the node/changeset ID.

SHA-1 digests are 20 bytes or 40 hex characters. They look
like ``835dbd9444dbed0cdc2ca27e23839f05a58e1dc1``. For readability,
these are almost always abbreviated to 12 characters in user-facing
interfaces. e.g. ``835dbd9444db``.

We can ask Mercurial to render these SHA-1 digests instead of the
commit messages::

   $ hg log -G -T '{node}'
   @  2bf9b23b2d0379540038866a72699a8ce5e92e84
   |
   o  0f165760af41ddde6470860088f421c1efcc5a5f
   |
   o  7175417717e87c88e4cf61ab2f76f2c54c76fa4b
   |
   o  8febb2b7339e5843832ab893ca2a002cd4394a03

Or we can ask for the short versions::

   $ hg log -G -T '{node|short} {desc}'
   @  2bf9b23b2d03 D
   |
   o  0f165760af41 C
   |
   o  7175417717e8 B
   |
   o  8febb2b7339e A

.. note::

   We start to use some more capabilities of Mercurial's *templates*
   feature. This allows output from Mercurial commands to be
   customized. See ``hg help templates`` for more.

Because SHA-1s (even their short versions) are difficult to remember,
we'll continue using commit messages and single letters throughout this
article to aid comprehension.

Important Properties from Using Hashing
---------------------------------------

Since node IDs are derived by hashing content, this means that changing
**any** of that content will result in the node ID changing.

Change a file: new node ID.

Change the commit message: new node ID.

Change the parent of a node: new node ID.

Changing the content of a changeset and thus its node ID is referred
to as *history rewriting* because it changes the *history* of a
repository/DAG. *History rewriting* is an important topic, but it won't
be discussed quite yet. The important thing to know is that if you
change anything that's part of the changeset, the node ID changes.

Moving Between Nodes
====================

Looking at the state of our Mercurial repository on the filesystem, we
see two entries::

   $ ls -A
   .hg/
   file

The ``.hg`` directory contains all the files managed by Mercurial. It should
be treated as a block box.

Everything else in this directory (currently just the ``file`` file and
the current directory) is referred to as the *working directory* or
*working copy* (both terms used interchangeably).

The *working directory* is based on the state of the files in a repository
at a specific changeset/node. We say *based on* because you can obviously
change file contents. But initially, the *working directory* matches exactly
what is stored in a specific changeset/node.

The ``hg update`` (frequently ``hg up``) command is used to change which
node in the DAG the *working directory* corresponds to.

If you ``hg up 7175417717e8``, the *working directory* will assume the state
of the files from changeset/node ``7175417717e8...``. If you
``hg up 2bf9b23b2d03``, state will be changed to ``2bf9b23b2d03...``.

The ability to move between nodes in the DAG introduces the possibility
to...

Creating DAG Branches
=====================

Up until this point, we've examined perfectly linear DAGs. As a refresher::

   $ hg log -G -T '{node|short} {desc}'
   @  2bf9b23b2d03 D
   |
   o  0f165760af41 C
   |
   o  7175417717e8 B
   |
   o  8febb2b7339e A

Every node (except the root, ``A``/``8febb2b7339e``) has 1 parent node.
And the graph as a whole has a single head (``D``/``2bf9b23b2d03``).

Let's do something a bit more advanced. We start by switching the
*working directory* to a different changeset/node::

   $ hg up 7175417717e8
   1 files updated, 0 files merged, 0 files removed, 0 files unresolved

   $ hg log -G -T '{node|short} {desc}'
   o  2bf9b23b2d03 D
   |
   o  0f165760af41 C
   |
   @  7175417717e8 B
   |
   o  8febb2b7339e A

(Note how ``@`` - the representation of the active changenode/node
in the *working directory* - moved from ``D`` to ``B``)

Now let's commit a new changeset/node::

  $ echo 5 >> file
  $ hg commit -m E
  created new head

That *created new head* message is a hint that our DAG has changed. Can
you guess what happened?

Let's take a look::

   $ hg log -G -T '{node|short} {desc}'
   @  4a3687e9313a E
   |
   | o  2bf9b23b2d03 D
   | |
   | o  0f165760af41 C
   |/
   o  7175417717e8 B
   |
   o  8febb2b7339e A

``B`` now has multiple direct children nodes, ``C`` and ``E``. In
graph terminology, we refer to this as a *branch point*.

``E`` has no children, so it is a *head* node (``D`` is still a
head node as well).

Because the visualization of the graph can resemble a tree (from
nature, not your computer science textbooks), small *protrusions*
from the main *trunk* are referred to as *branches* from the
perspective of the DAG. (Mercurial has overloaded *branch* to convey
additional semantics, so try not to confuse a *DAG branch* with
a *Mercurial branch*.)

The *created new head* message was Mercurial telling us that we
created not only a a new *DAG head* but also a new *DAG branch*.

Because your commit is taking the repository in a different
*direction* (very non-scientific word), this act of creating new
DAG branches is sometimes referred to as *divergence* or *diverging*.

DAG branches turn out to be an excellent way to work on separate
and isolated units of change. These are often referred to as
*feature branches* because each DAG branch consists of a specific
feature. For more, see :ref:`hgmozilla_workflows`.

It's worth nothing that ``hg commit`` **always** produces a new head
node because the node being created never has any children. However,
it may not create a new DAG branch: a new DAG branch is only created
when the parent node of the commit isn't a head node.

Before we go on let's commit a new changeset on top of ``E`` to make
the DAG branch more pronounced::

   $ echo 6 >> file
   $ hg commit -m F

   $ hg log -G -T '{node|short} {desc}'
   @  da36621d7a94 F
   |
   o  4a3687e9313a E
   |
   | o  2bf9b23b2d03 D
   | |
   | o  0f165760af41 C
   |/
   o  7175417717e8 B
   |
   o  8febb2b7339e A

Merging DAG Branches
====================

Now that we have multiple DAG branches, it is sometimes desirable to
*merge* them back into a 1. The Mercurial command for performing this
action is ``hg merge``.

Let's change our working directory to the changeset that we want to
merge *into*. We choose ``D``, since it was our original head.::

   $ hg up 2bf9b23b2d03
   1 files updated, 0 files merged, 0 files removed, 0 files unresolved

Now we tell Mercurial to bring the changes from ``F``'s head into
``D``'s::

   $ hg merge da36621d7a94
   0 files updated, 1 files merged, 0 files removed, 0 files unresolved
   (branch merge, don't forget to commit)

   $ hg commit -m G

Visualizing the result::

   $ hg log -G -T '{node|short} {desc}'
   @    19c6c94d7bb2 G
   |\
   | o  da36621d7a94 F
   | |
   | o  4a3687e9313a E
   | |
   o |  2bf9b23b2d03 D
   | |
   o |  0f165760af41 C
   |/
   o  7175417717e8 B
   |
   o  8febb2b7339e A

``G``/``19c6c94d7bb2`` is what is referred to as a *merge commit*. It
is the result of a commit operation that merged 2 nodes. From the
perspective of the DAG, it is a node with 2 parents, not 1.

Conclusion
==========

These are the basics of how Mercurial uses a directed acyclic graph
(DAG) to represent repository history.

If you would like to learn more about how distributed version control
systems (like Mercurial) use DAGs, please read
`this article <http://ericsink.com/entries/dvcs_dag_1.html>`_.

For more on workflows that build upon this knowledge, see
:ref:`hgmozilla_workflows`.
