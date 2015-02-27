.. _hgmo_managing_repos:

=====================
Managing Repositories
=====================

``hg.mozilla.org`` has a self-service mechanism for managing some
repositories on the server.

Overview
========

You can SSH into ``hg.mozilla.org`` and execute specific commands
to perform repository management. You don't get a full shell. Instead,
you will be interfacing with an interactive wizard that will guide
you through available options.

What Repositories Can Be Managed
================================

Currently, the self-service interface only allows management of
*user repositories*. These are repositories under
https://hg.mozilla.org/users/.

For management of non-user repositories, please file a
`Developer Services :: hg.mozilla.org <https://bugzilla.mozilla.org/enter_bug.cgi?product=Developer%20Services&component=Mercurial%3A%20hg.mozilla.org>`_
bug.

Who Has Access
==============

Any account with
`level 1 commit access <https://www.mozilla.org/hacking/commit-access-policy/#Summary>`_
can push to user repositories and can manage their own user repositories.

When to Use a User Repository
=============================

``hg.mozilla.org`` server operators have a reluctant tolerance towards
the existence of user repositories on hg.mozilla.org.

In the ideal world, Mozilla is not a generic repository hosting service
and hosting of non-critical repositories would be pushed off to free
service hosting providers, such as Bitbucket. One reason is performance:
user repositories take resources that could otherwise be put towards
making other services and repositories faster.

However, there are some scenarios where third party hosting providers
won't fulfill developer needs.

.. important::

   Unless you have a specific need that requires hosting on hg.mozilla.org,
   you should consider hosting your repository on another service instead
   of hg.mozilla.org.

Configuring
===========

You will need to configure your SSH client to talk to ``hg.mozilla.org``.
See :ref:`auth_ssh` for instructions.

Creating a User Repository
==========================

A new repository can be created by running the ``clone <repo>`` command.
e.g.::

   $ ssh hg.mozilla.org clone my-new-repo

An interactive wizard will guide you through the process that should be
self-expanatory. You'll have the option of creating an empty repository
or cloning (forking) from an existing repository.

.. important::

   Creating repositories can sometimes take many minutes. Do not ctrl+c
   the operation or the servers may be left in an inconsistent state.

   If you encounter a problem, file a bug or say something in ``#vcs``
   on IRC.

Editing a User Repository
=========================

It is possible to configure a number of options on repositories. The
common interface for all actions is to run ``edit <repo>``. e.g.::

   $ ssh hg.mozilla.org edit my-repo

An interactive wizard will guide you through available options. Some
of those options are described below.

Repository Description
----------------------

It is possible to edit the repository's *description*. This is text that
appears in the repository listing at https://hg.mozilla.org/.

.. tip::

   We recommend always defining a description so people know what your
   repository is used for.

Publishing and Non-Publishing Repositories
------------------------------------------

Mercurial has a feature called *phases* that prevents changesets that
have been *published* from being mutated (deleted, rewritten, etc). It
prevents a foot gun where you could accidentally rewrite history
that has been shared with others, which would result in divergent
branches and confusion.

By default, Mercurial repositories are *publishing*, which means that
anything pushed gets published (bumped to the *public* phase in technical
terms) and Mercurial clients won't let you change those commits.

.. important::

   User repositories on hg.mozilla.org are non-publishing by default.

If you would like to change whether your repository is publishing or
non-publishing, use the ``edit <repo>`` command and select the
appropriate option.

Deleting a User Repository
==========================

To delete a user repository, run ``edit <repo>`` and select the
``delete`` option.

User Repository URLs
====================

Your own user repositories are accessible under the following URLs:

   ssh://hg.mozilla.org/users/<username>/<repo> (read/write)
   https://hg.mozilla.org/users/<username>/<repo> (read only)

Your SSH/LDAP username is normalized. Specifically, the ``@`` in your
email address is normalized to ``_``. e.g. ``mary@example.com``
becomes ``mary_example.com``.

When you create a user repository, you probably want to set up some
paths in your hgrc. Here is an example ``.hg/hgrc``::

   [paths]
   default = https://hg.mozilla.org/users/me_example.com/my-repo
   default-push = ssh://hg.mozilla.org/users/me_example.com/my-repo
