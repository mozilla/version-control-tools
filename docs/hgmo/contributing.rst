.. _hgmo_contributing:

============
Contributing
============

Repositories and Relevant Files
===============================

Most code for hg.mozilla.org and related services can be found in the
`version-control-tools repo <https://hg.mozilla.org/hgcustom/version-control-tools>`_.
In this repo, the following directories are relevant:

ansible/roles/hg-ssh
   Ansible role for the hg.mozilla.org SSH/master servers.
ansible/roles/hg-ssh-server
   Shared Ansible role for Mercurial SSH servers.
ansible/roles/hg-web
   Ansible role for the hg.mozilla.org HTTP/mirror servers.
docs/hgmo
   Sphinx documentation related to hg.mozilla.org (you are reading this now).
hgext
   Various Mercurial extensions. Many of which are used on hg.mozilla.org.
hgext/hgmo
   Contains hodgepodge of Mercurial customizations specific to hg.mozilla.org.
hghooks
   Mercurial hooks that run (primarily) on hg.mozilla.org.
hgserver
   Mercurial code and tests specific to Mercurial servers.
hgtemplates
   Mercurial templates. Contains both upstream templates and Mozilla
   customizations.
hgtemplates/gitweb_mozilla
   Fork of the ``gitweb`` Mercurial web style with Mozilla customizations.
   If you want to hack the theming on hg.mozilla.org, this is what you
   modify.
hgwsgi
   WSGI and Mercurial config files for repos on hg.mozilla.org.
pylib/mozautomation
   Python package containing utility code for things like defining names
   and URLs of common repos, parsing commit messages, etc.
pylib/mozhg
   Python package containing shared Mercurial code (code using Mercurial
   APIs and therefore covered by the GPL).
pylib/vcsreplicator
   Code for managing replication of data from Mercurial master server
   to read-only mirrors.

Terraform code for managing associated AWS infrastructure can be found
in the
`devservices-aws repo <https://github.com/mozilla-platform-ops/devservices-aws>`_
under the ``hgmo`` directory.

Hacking the Theming
===================

The version-control-tools repository contains all the files necessary
to run a local ``hgweb`` server that behaves close enough to the actual
server to facilitate hacking on the theming (the visual layout of the
site).

To run a local server, run the following::

   $ hg --config extensions.hgmo=/path/to/vct/hgext/hgmo serve --hgmo

Among other things, the ``hgmo`` extension adds a flag to ``hg serve``
that activates *hg.mozilla.org mode*. This will activate some other
extensions and configure the style settings to run out of the
version-control-tools repository.

Styles for Mercurial are checked into the ``hgtemplates/`` directory
in version-control-tools. The default style for Mercurial is ``paper``.
However, hg.mozilla.org runs the ``gitweb_mozilla`` theme. This theme is
based off of the ``gitweb`` theme.

The ``hgtemplates/gitweb_mozilla/map`` file is the main file mapping
template names to their values. Some templates are large and split into
their own ``.tmpl`` file.

.. hint::

   To figure out what templates are used for various URLs, read
   ``hg help hgweb``.

.. hint::

   If you modify a template file, changes should be visible on next page
   load: no server restart is necessary. However, some pages are cached,
   so you may need to force reload the page in your browser via
   shift-reload or similar.
