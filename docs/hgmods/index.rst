.. _hgmods:

========================
Mercurial Customizations
========================

This repository contains numerous customizations to the
`Mercurial <https://www.mercurial-scm.org/>`_ version control tool.

.. toctree::
   :maxdepth: 2

   extensions
   hooks

Creating and Maintaining a Development Environment
==================================================

In order to run tests for the extensions and hooks, you'll need to create
and activate an isolated environment.

From the root directory of a version-control-tools checkout::

   $ ./create-environment hgdev

Or to create an environment with support for running Bugzilla tests
requiring Docker::

   $ ./create-environment hgdev --docker-bmo

This will create a Python virtualenv in ``venv/hgdev``. Assuming all
goes well, it will print instructions on how to *activate* that
environment in your local shell and how to run tests.

If the command fails, a likely culprit is missing system package
dependencies.

On Debian/Ubuntu based distros, install required system packages via::

   $ apt-get install build-essential python-all-dev sqlite3

On RedHat/CentOS based distros::

   $ yum install bzip2 gcc python-devel sqlite

Then try ``./create-environment hgdev`` again. If that fails, this
documentation may need updated!
