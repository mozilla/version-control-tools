.. _hgmozilla_extensions:

=====================================
Installing and Configuring Extensions
=====================================

A vanilla install of Mercurial does not have many features. This is an
intentional choice by Mercurial to keep the base install simple and free
of foot guns.

Installing Extensions
=====================

To install an extension, you'll need to add a line to your Mercurial
configuration file.

As a user, you care about the following configuration files:

1. Your global hgrc
2. A per-repository hgrc

Your user-global configuration file is ``~/.hgrc``. Settings in this
file apply to all ``hg`` commands you perform everywhere on your system
(for your current user).

Each repository that you clone or initialize has an optional
``.hg/hgrc`` file that provides repository-specific configurations.

Mercurial starts by loading and applying settings from global
configuration files and then overlays configurations from each
lesser-scoped files.

.. tip::

   To learn more about Mercurial configuration files, run ``hg help
   config``.

To install an extension, you add a line under the ``[extensions]``
section of a config file like the following::

  [extensions]
  foo=path/to/extension

This is saying *activate the **foo** extension whose code is present at
**path/to/extension***.

Core Extensions That Almost Everyone Wants
==========================================

Mercurial ships with a number of built-in extensions. Of these, every
user will almost always want to install the following extensions:

color
   This extension adds colorized output to commands, making output
   easier to read.
pager
   Enable command output to go to a pager (such as less).
progress
   Show progress bars during long-running operations.

Since core extensions are bundled with Mercurial, they have a special
syntax that makes them easier to install::

  [extensions]
  color=
  pager=
  progress=

Core Extensions to Perform History Rewriting
============================================

Out of the box, Mercurial only allows commits operations to be additive.
If you make a mistake, the solution is to create a new commit that fixes
it. You can't rewrite old commits. You can't change the order of
existing commits. You can't change the shape of the DAG of the commits.

These operations all have something in common: they rewrite history.

.. note::

   Mercurial doesn't allow history rewriting by default because it is a
   major foot gun for people new to version control. A potential
   side-effect of history rewriting is data loss or confusion due to
   loss of state. Mercurial believes that these risks should be opt-in
   and has thus shipped without any history rewriting features enabled
   by default.

Mercurial ships with a number of built-in extensions that enable history
rewriting:

histedit
   Enables the ``hg histedit`` command, which brings up a text editor
   listing commits, allowing you to change order and specify actions to
   perform.

   The functionality is roughly equivalent to ``git rebase -i``.
rebase
   Enables the ``hg rebase`` command, which allows you to splice commits
   across different chains in the DAG.
strip
   Enables you to delete changesets completely.

Core Extensions to Enable Different Workflows
=============================================

Mercurial ships with some extensions that enable alternate workflows.
These include:

mq
   Treat commits like a stack of patches and work on single patches at a
   time.
shelve
   Enables uncommitted work to be saved to a standalone file without
   being committed to the repository.
