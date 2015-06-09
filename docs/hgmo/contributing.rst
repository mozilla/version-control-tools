.. _hgmo_contributing:

============
Contributing
============

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
