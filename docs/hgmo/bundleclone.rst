.. _hgmo_bundleclone:

==================================
Cloning from Pre-Generated Bundles
==================================

``hg.mozilla.org`` supports offloading clone requests to pre-generated
bundle files stored in Amazon S3. This results in drastically reduced server
load and frequently results in faster clone times.

How It Works
============

When a Mercurial client clones a repository, it looks to see if the
server is advertising a list of available, pre-generated bundle files.
If it is, it looks at the list, finds the most appropriate entry,
downloads and applies that bundle, then does the equivalent of an ``hg
pull`` against the original Mercurial server to fetch new data since the
time the bundle file was produced. The end result is a faster clone with
drastically reduced load on the Mercurial server.

Enabling
========

To enable cloning from pre-generated bundles, you'll need to install the
`bundleclone extension <https://hg.mozilla.org/hgcustom/version-control-tools/file/default/hgext/bundleclone/__init__.py>`_.
Simply download that file then add the following to your global hgrc
file (likely ``/etc/mercurial/hgrc``)::

   [extensions]
   bundleclone = /path/to/bundleclone.py

.. tip::

   You can rename the ``__init__.py`` file as you see fit.

.. note::

   Functionality from the ``bundleclone`` extension is being added to
   core Mercurial. Eventually, a vanilla Mercurial install will be able
   to do everything ``bundleclone`` can do today.

Configuring
===========

By default, the first entry in the bundles file list will be used. The
server is configured so the first entry is the best choice for the most
people. However, various audiences will want to prioritize certain
bundles over others.

The ``bundleclone`` extension allows the client to define preferences
for which bundle to fetch. The way this works is the client defines some
key-value pairs and it upweights entries having these attributes. Read
the source of the ``bundleclone`` extension for more.

On ``hg.mozilla.org``, we define the following attributes:

ec2region
   The EC2 region the bundle file should be served from. We support
   ``us-west-2`` and ``us-east-1``. You should prefer the region that is
   closest to you.

compression
   The compression mode used in the bundle. ``gzip`` is the default.
   ``bzip2`` is available if you want to transfer less data but utilize
   more CPU cycles to clone.

stream
   Indicates that a *stream bundle* is available. These files are
   essentially tar archives. They typically run 30-50% larger than the
   default ``gzip`` bundles, but they consume 4-6x less CPU time to
   process.

If you are a Mozilla contributor in California, the defaults are
probably fine.

If you are a Mozilla contributor in Europe, you may want to prefer the
``us-east-1`` EC2 region like so::

   [bundleclone]
   prefers = ec2region=us-east-1

If you are in EC2, you should **always** pin your EC2 region as the
first entry. You should also prefer *stream bundle* mode, as network
bandwidth is plentiful and clones will be faster. e.g.::

   [bundleclone]
   prefers = ec2region=us-west-2, stream=revlogv1

.. important::

   If you have machinery in an EC2 region where we don't host bundles,
   please let us know. There's a good chance that establishing bundles
   in your region is cheaper than paying the cross-region transfer costs
   (intra-region transfer is free).

Which Repositories Have Bundles Available
=========================================

Bundles are automatically generated for repositories that are high
volume (in terms of repository size and clone frequency) or have a need
for bundles.

If you have the ``bundleclone`` extension installed and Mercurial doesn't
print information about downloading a bundle file when you ``hg clone``
from ``hg.mozilla.org``, bundles probably aren't being generated for
that repository.

If you think bundles should be made available, let a server operator
know by filing a ``Developer Services :: hg.mozilla.org`` bug or by joining
#vcs on irc.mozilla.org.
