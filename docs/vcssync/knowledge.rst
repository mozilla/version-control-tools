.. _vcssync_knowledge:

=====================
Accumulated Knowledge
=====================

Over the years, Mozilla has had to deploy numerous solutions for rewriting
and synchronizing the history of various version control repositories.
Synchronization is an inherently difficult problem and as one can expect,
we've learned a lot through trial and error. This document serves to capture
some of that knowledge.

Thoughts on ``git filter-branch``
=================================

``git filter-branch`` is Git's built-in tool for complex repository history
rewriting. It accepts as arguments *filters* - or executables or scripts -
to perform actions at specific stages. e.g. *rewrite the commit message* or
*modify the files in a commit*.

While ``git filter-branch`` generally gets the job done for simple, one-time
rewrites, we've found that it isn't suitable for a) rewriting tree content
(read: files in commits) of large repositories b) use in incremental
conversion scenarios c) where robustness or complete control is needed or
d) where performance is important.

The following are some of the deficiencies we've encountered with
``git filter-branch``:

Index update performance
   Rewriting files in history using ``git filter-branch`` requires either
   a ``--tree-filter`` or an ``--index-filter`` (there is a
   ``--subdirectory-filter`` but it is internally implemented as an
   index filter of sorts).

   ``--tree-filter`` should be avoided at all costs because having to perform
   a working copy *sync* on every commit adds a lot of overhead. This is
   especially true in scenarios where you are removing a large directory
   from history. e.g. if you are rewriting history to remove 10,000 files
   from a directory, each commit processed by ``--tree-filter`` will need
   to repopulate the files from that directory on disk. That's **extremely**
   slow.

   ``--index-filter`` is superior to ``--tree-filter`` in that it only needs
   to populate the Git index on every commit (as opposed to the working copy).
   This is substantially faster. But, our experience is that ``--index-filter``
   is still a bit slow.

   Writing the index requires I/O (it is a file). Some index update operations
   also require I/O (to e.g. ``stat()`` paths). For this reason, if using an
   ``--index-filter``, it is highly recommended to perform operations on a
   tmpfs volume (``-d`` argument). Failure to do so could result in significant
   slowdown due to waiting on filesystem I/O.

   When rewriting large parts of the index, we found the performance of
   ``git update-index`` against the existing index to be a bit slow. This is
   even when using ``--assume-unchanged`` to prevent verifying changes with
   the filesystem. In some cases (including one where we deleted 90% of the
   files in a repository), we found that writing a new index file from
   scratch (by setting the ``$GIT_INDEX_FILE`` environment variable combined
   with ``git update-index --index-info`` to produce a new index file) then
   replacing the existing index was filter than updating the index in place.

   We also found the best way to load entries into an index was via
   ``git update-index -z --index-info``.

Overhead of filter invocation
   Every ``--filter-*`` argument passed to ``git filter-branch`` invokes a
   process for every commit. If you have 4 filters and 10,000 commits, that's
   40,000 new processes. If your process startup overhead is 10ms (typical
   for Python processes), that's 400s right there - and your processes haven't
   even done any real work yet! By the time you factor in the filter processes
   doing something, you could be spending dozens of minutes in filters for
   large repositories.

Complexity around incremental rewriting
   We often want to perform incremental, ongoing rewriting of a repository. For
   example, we want to remove a directory and publish the result to a separate
   repo. ``git filter-branch`` can be coerced to do this, but it requires a bit
   of work.

   ``git filter-branch`` is given a *rev-list* of commits to operate on. When
   doing an incremental rewrite, you need to specify the base commits to
   *anchor* how far back processing should go. For simple histories, specifying
   ``base..head`` *just works*. However, things quickly fall apart in more
   complicated scenarios. Imagine this history::

     E
     | \
     D  F
     |  |
     C  |
     | /
     B
     |
     A

   If we initially converted ``C``, the next conversion could naively specify a
   *rev-list* of ``C..E``. This would include ``F`` since it is an ancestor of
   ``E``. It would also pull in ``B`` and ``A`` since those are ancestors of
   ``F``. This would mean that ``git filter-branch`` would redundantly operate
   on ``A`` and ``B``! In the best case, this would lead to overhead and slow
   down incremental operations. In the worst case it would lead to divergent
   history. Not good.

   This problem can be avoided by using the ``^COMMIT`` syntax in the *rev-list*
   to exclude a commit and any of its ancestors. If your repository has very
   complicated history, you may need to specify ``^COMMIT`` multiple times,
   one for each known root in the unconverted *incoming* set of commits.

   Another problem with incremental operations is grafting *incoming*
   commits onto the appropriate commit from the last run. Unless you take
   action, ``git filter-branch`` will parent your new commit in the *source*
   DAG, which is not what you want for incremental conversions!

   While you can solve this problem with a ``--parent-filter`` to rewrite
   parents of processed commits, we found this approach too complicated.
   Instead, before incremental conversion, we walked the DAG of the
   to-be-processed commits. For each root node in that sub-graph, we created
   a Git graft (using the ``info/grafts`` file) mapping the old parent(s)
   to the already-converted parents. The ``info/grafts`` file was only
   modified for the duration of ``git filter-branch``. A benefit of this
   approach over ``--parent-filter`` was you only need to process the graft
   mapping once before conversion, as opposed for every commit. This
   mattered for performance.

Ignoring commits from outside first parent ancestry
   One of our common repository rewriting scenarios is stripping out merge
   commits from a repository (we like linear history). It is possible to do
   this with ``git filter-branch`` by using a ``--parent-filter`` that simply
   only returns the first parent.

   However, there is no easy way to tell ``git filter-branch`` to only
   convert the first parent ancestry. While ``git log`` has a
   ``--first-parent`` argument, there is no *rev-list* syntax to do this.
   And, listing each first parent commit explicitly will exhaust argument
   length for large repositories.

   So, you either have to call ``git filter-branch`` in batches with single
   commits or have to live with ``git filter-branch`` converting commits not
   in the first parent ancestry. The latter can have major performance
   implications (e.g. you process 80% more commits than you need to).

Control over refs
   ``git filter-branch`` automatically updates the source ref it is converting.
   This is slightly annoying.

``git filter-branch`` seems like an appropriate tool for systematic repository
rewriting. But our experiences tell us otherwise. If you are a developer and
need it for a quick one-off or if you are performing a one-time rewrite, it's
probably fine. But for ongoing, robust rewriting, it's far from our first
choice.

A case study demonstrating our lack of content for ``git filter-branch`` is
converting the history of the Servo repository to Mercurial so we could
vendor it into Firefox. This conversion had a few requirements:

* We wanted to strip a few directories containing 100,000+ files
* We wanted to *linearize* the history so there were no merges
* We wanted to rewrite the commit message
* We wanted to insert hidden metadata in the commit object so ``hg convert``
  would treat it properly

This was initially implemented with ``git filter-branch`` using 4 filters:
*parent*, *msg*, *index*, and *commit*. The *parent* filter was implemented
with ``sed``. The rest were Python scripts. Rewriting ~23,000 commits
with ``git filter-branch`` took almost 2 hours. That was after spending
considerable time to optimize the index filter to run as fast as possible
(including doing nothing if the current commit wasn't in first parent
ancestry). Without these optimizations and tmpfs, run-time was 5+ hours!

After realizing that we were working around ``git filter-branch`` more than
it was helping us, we rewrote all the functionality in Python, building on
top of the *Dulwich* package - a Python implementation of the Git file
formats and protocols - *Dulwich*:

* Gave us full control over which commits were processed. No more complexity
  around incremental operations!
* Allowed us to perform all operations against rich data structures (as opposed
  to parsing state from filter arguments, environment variables, or by running
  ``git`` commands). This was drastically simpler (assume you have knowledge of
  Git's object types and how they work) and faster to code.
* Allowed us to use a single Python process for rewriting. This eliminated all
  new process overhead from ``git filter-branch``.
* Allowed us to bypass the index completely. Instead, we manipulated Git *tree*
  objects in memory. While more complicated, this cut down on significant
  overhead.
* Drastically reduced I/O. Most of this was from avoiding the index. With
  Dulwich, the only I/O was object reads and writes, which are pretty fast.
* Guaranteed better consistency. When using ``git`` commands, things like
  environment variables and ``~/.gitconfig`` files matter. With Dulwich, this
  magic wasn't in play and execution is much more tolerable of varying
  environments.

It took ~4 hours to rewrite the ``git filter-branch`` based solution to use
Dulwich. This was made far easier by the fact that our filters were implemented
in Python before. The effort was worth it: **Python + Dulwich performed an
identical conversion of the Servo repository in ~10s versus ~2 hours** - a
~700x speedup.

Converting from Git to Mercurial
================================

Git and Mercurial have remarkably similar concepts for structuring commit
data. Essentially, both have commit objects a) with a link to a tree or
manifest of all files as they exist in that commit b) links to parent commits.
Not only is conversion between Git and Mercurial repositories possible, but
numerous tools exist for doing it!

While there are several tools that can perform conversions, each has its
intended use cases and gotchas.

In many cases ``hg convert`` for performing an unidirectional conversion of
Git to Mercurial *just works* and is arguably the tool best suited for the
job (on the grounds that Mercurial itself knows the best way for data to
be imported into it). That being said, we've run into a few scenarios where
``hg convert`` on its own isn't sufficient::

Removing merges from history
   We sometimes want to remove merge commits from Git history as part of
   converting to Mercurial. ``hg convert`` doesn't handle this case well.

   In theory, you can provide ``hg convert`` a splice map that instructs
   the conversion to remove parents from a merge. And, ``hg convert`` happily
   parses this and starts converting away. But it will eventually explode
   in a few places where it assumes all parents of a source commit exist in
   the converted history. This could likely be fixed upstream.

Copy/rename detection performance
   Mercurial stores explicit copy and rename metadata in file history. Git
   does not. So when converting from Git to Mercurial, ``hg convert`` asks
   Git to resolve copy and rename metadata, which it then stores in
   Mercurial. This more or less *just works*.

   A problem with resolving copy and rename metadata is it is very
   computationally expensive. When Git's ``--find-copies-harder`` flag
   is used, Git examines *every* file in the commit/tree to find a copy
   source. For repositories with say 100,000 files, you can imagine how
   slow this can be.

   Sometimes we want to remove files as part of conversion. If doing the
   removal inside ``hg convert``, ``hg convert`` will have Git perform
   the copy and rename detection *before* those discarded files are
   removed. This means that Git does a lot of throwaway work for files
   that aren't relevant. When removing tens of thousands of files, the
   overhead can be staggering.

Copy/rename metadata and deleted files
   As stated above, Mercurial stores explicit copy and rename metadata in
   file history. When files are being deleted by ``hg convert``, there
   appears to be some problems where ``hg convert`` gets confused if
   the copy or rename source resides in a deleted file. This is almost
   certainly a correctable bug in ``hg convert``.

Behavior for empty changesets
   When removing files from history (including ignoring Git submodules), it
   is possible for the converted Git commit to be empty (no file changes).

   ``hg convert`` has (possibly buggy) behavior where it automatically
   discards empty changesets, but only if a ``--filemap`` is being used.
   This means that empty Git commits are preserved unless ``--filemap`` is
   used. (A workaround is to specify ``--filemap /dev/null``.)

When these scenarios are in play, we've found that it is better to
perform the Git to Mercurial conversion in 2 phases:

1. Perform a Git->Git rewrite
2. Convert the rewritten Git history to Mercurial

In cases where lots of files are being removed from Git history, this
approach is *highly* recommended because of the performance overhead of
processing the unwanted files during ``hg convert``.
