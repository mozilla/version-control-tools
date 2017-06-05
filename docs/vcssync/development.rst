.. _vcssync_development:

=================
Development Guide
=================

Repositories and Relevant Code
==============================

Most code related to version control syncing is in the
`version-control-tools repo <https://hg.mozilla.org/hgcustom/version-control-tools>`_.
In this repository, the following directories are relevant:

ansible/roles/vcs-sync
   Ansible role for version control sync server.
docs/vcssync
   Sphinx documentation for everything related to version control
   synchronization (you are reading this now).
vcssync
   Python package containing code and services for everything related
   to version control synchronization.

Code reviews for everything in version-control-tools should be conducted
with MozReview. Reviews should be directed at ``gps`` or ``glob``.

Terraform configs for AWS infrastructure for VCS Sync lives in the
`devservices-aws repo <https://github.com/mozilla-platform-ops/devservices-aws>`_,
specifically in the ``vcssync`` directory. Change proposals are submitted
via GitHub Pull Requests. Reviews are typically handled by someone
on the Ops Team, namely ``fubar``, ``dividehex``, or ``dhouse. For new
infrastructure, ``gps`` or ``glob`` should likely take a look.

Creating a Development and Testing Environment
==============================================

From a fresh ``version-control-tools`` checkout, run the following to create
a development and testing environment::

   $ ./create-environment vcssync

Then activate the environment in your shell via::

   $ source activate venv/vcssync/bin/activate

Running Tests
=============

To run the vcssync tests, run::

   $ ./run-tests -j4

Using Betamax for HTTP Request Replaying
========================================

We use the `Betamax <http://betamax.readthedocs.io/>`_ Python package
to facilitate testing HTTP requests against various services, such as
the GitHub API.

When the ``BETAMAX_LIBRARY_DIR`` and ``BETAMAX_CASSETTE`` environment
variables are defined, Betamax is configured to use the cassette
(recording of HTTP interactions) specified. Betamax's record mode is
set to ``none``, which means that only HTTP interactions saved in the
cassette are allowed.

The ``vcssync/tests/record_cassettes.py`` script is used to record
cassettes (read: perform actual interactions with real servers and
save the results). Run this script from an activated virtualenv to
create/update/re-record cassettes. Minor changes in the cassettes
(such as dates and request IDs) are expected to change. Other things
may change over time and changes should be scrutinized during review.

``record_cassettes.py`` requires a GitHub API token. Go to
https://github.com/settings/tokens/new to generate one. It should only
need minimal privileges. While the cassettes shouldn't save your token,
it is a good practice to delete the token once you're done recording
cassettes.
