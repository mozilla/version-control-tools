.. _hgmo_bundleclone:

==================================
Cloning from Pre-Generated Bundles
==================================

``hg.mozilla.org`` supports offloading clone requests to pre-generated
bundle files stored in Amazon S3. **This results in drastically reduced
server load (which helps prevent outages due to accidental, excessive
load) and frequently results in faster clone times.**

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

If you are running Mercurial 3.6.1 or newer, support for cloning from
pre-generated bundles is built-in to Mercurial itself. However, it
requires enabling a config option::

   [experimental]
   clonebundles = true

If you are running a Mercurial older than 3.6, first please consider
upgrading to 3.6.1 or newer, as 3.6 contains a number of performance
enhancements to cloning. If you absolutely must run a Mercurial older
than 3.6, you can install the
`bundleclone extension <https://hg.mozilla.org/hgcustom/version-control-tools/file/default/hgext/bundleclone/__init__.py>`_.
Simply `download
<https://hg.mozilla.org/hgcustom/version-control-tools/raw-file/default/hgext/bundleclone/__init__.py>`_
that file then add the following to your global hgrc file (likely
``/etc/mercurial/hgrc``)::

   [extensions]
   bundleclone = /path/to/bundleclone.py

.. tip::

   You can rename the ``__init__.py`` file as you see fit.

Configuring
===========

By default, the first entry in the bundles file list will be used. The
server is configured so the first entry is the best choice for the most
people. However, various audiences will want to prioritize certain
bundles over others.

Both the built-in *clone bundles* feature and *bundleclone* allow the
client to define preferences of which bundles to fetch. The way this
works is the client defines some key-value pairs in its config and
bundles having these attributes will be upweighted.

On ``hg.mozilla.org``, we define the following attributes are defined in
the manifest:

BUNDLESPEC (clonebundles only)
   This defines the type of bundle.

   We currently generate bundles with the following specifications:
   ``gzip-v1``, ``bzip2-v1``, ``none-packed1``.

REQUIRESNI (clonebundles only)
   Indicates whether the URL requires SNI (a TLS extension). This is set
   to ``true`` for URLs where multiple certificates are installed on the
   same IP and SNI is required. It is undefined if SNI is not required.

requiresni (bundleclone only)
   This behaves exactly the same as ``REQUIRESNI``. It is how
   *bundleclone* defines the SNI requirement.

ec2region (clonebundles and bundleclone)
   The EC2 region the bundle file should be served from. We support
   ``us-west-2`` and ``us-east-1``. You should prefer the region that is
   closest to you.

compression (bundleclone only)
   The compression mode used in the bundle. ``gzip`` is the default.
   ``bzip2`` is available if you want to transfer less data but utilize
   more CPU cycles to clone.

   This metadata is captured by the ``BUNDLESPEC`` attribute when using
   the built-in clone bundles feature.

stream (bundleclone only)
   Indicates that a *stream bundle* is available. These files are
   essentially tar archives. They typically run 30-50% larger than the
   default ``gzip`` bundles, but they consume 4-6x less CPU time to
   process.

   This is captured by the ``BUNDLESPEC`` attribute in *clone bundles*.

cdn (clonebundles and bundleclone)
   Indicates whether the URL is on a CDN. Value is ``true`` to indicate
   the URL is a CDN. All other values or undefined values are to be
   interpretted as not a CDN.

Here is an example *clone bundles* manifest::

   https://hg.cdn.mozilla.net/mozilla-central/4a7526d26bd47ce2e01f938702b91c95424026ed.gzip.hg BUNDLESPEC=gzip-v1 REQUIRESNI=true cdn=true
   https://s3-us-west-2.amazonaws.com/moz-hg-bundles-us-west-2/mozilla-central/4a7526d26bd47ce2e01f938702b91c95424026ed.gzip.hg BUNDLESPEC=gzip-v1 ec2region=us-west-2
   https://s3-external-1.amazonaws.com/moz-hg-bundles-us-east-1/mozilla-central/4a7526d26bd47ce2e01f938702b91c95424026ed.gzip.hg BUNDLESPEC=gzip-v1 ec2region=us-east-1
   https://hg.cdn.mozilla.net/mozilla-central/4a7526d26bd47ce2e01f938702b91c95424026ed.bzip2.hg BUNDLESPEC=bzip2-v1 REQUIRESNI=true cdn=true
   https://s3-us-west-2.amazonaws.com/moz-hg-bundles-us-west-2/mozilla-central/4a7526d26bd47ce2e01f938702b91c95424026ed.bzip2.hg BUNDLESPEC=bzip2-v1 ec2region=us-west-2
   https://s3-external-1.amazonaws.com/moz-hg-bundles-us-east-1/mozilla-central/4a7526d26bd47ce2e01f938702b91c95424026ed.bzip2.hg BUNDLESPEC=bzip2-v1 ec2region=us-east-1
   https://hg.cdn.mozilla.net/mozilla-central/4a7526d26bd47ce2e01f938702b91c95424026ed.packed1.hg BUNDLESPEC=none-packed1;requirements%3Drevlogv1 REQUIRESNI=true cdn=true
   https://s3-us-west-2.amazonaws.com/moz-hg-bundles-us-west-2/mozilla-central/4a7526d26bd47ce2e01f938702b91c95424026ed.packed1.hg BUNDLESPEC=none-packed1;requirements%3Drevlogv1 ec2region=us-west-2
   https://s3-external-1.amazonaws.com/moz-hg-bundles-us-east-1/mozilla-central/4a7526d26bd47ce2e01f938702b91c95424026ed.packed1.hg BUNDLESPEC=none-packed1;requirements%3Drevlogv1 ec2region=us-east-1

And here is the same logic manifest but for *bundleclone*::

   https://hg.cdn.mozilla.net/mozilla-central/4a7526d26bd47ce2e01f938702b91c95424026ed.gzip.hg compression=gzip cdn=true requiresni=true
   https://s3-us-west-2.amazonaws.com/moz-hg-bundles-us-west-2/mozilla-central/4a7526d26bd47ce2e01f938702b91c95424026ed.gzip.hg ec2region=us-west-2 compression=gzip
   https://s3-external-1.amazonaws.com/moz-hg-bundles-us-east-1/mozilla-central/4a7526d26bd47ce2e01f938702b91c95424026ed.gzip.hg ec2region=us-east-1 compression=gzip
   https://hg.cdn.mozilla.net/mozilla-central/4a7526d26bd47ce2e01f938702b91c95424026ed.bzip2.hg compression=bzip2 cdn=true requiresni=true
   https://s3-us-west-2.amazonaws.com/moz-hg-bundles-us-west-2/mozilla-central/4a7526d26bd47ce2e01f938702b91c95424026ed.bzip2.hg ec2region=us-west-2 compression=bzip2
   https://s3-external-1.amazonaws.com/moz-hg-bundles-us-east-1/mozilla-central/4a7526d26bd47ce2e01f938702b91c95424026ed.bzip2.hg ec2region=us-east-1 compression=bzip2
   https://hg.cdn.mozilla.net/mozilla-central/4a7526d26bd47ce2e01f938702b91c95424026ed.stream-legacy.hg stream=revlogv1 cdn=true requiresni=true
   https://s3-us-west-2.amazonaws.com/moz-hg-bundles-us-west-2/mozilla-central/4a7526d26bd47ce2e01f938702b91c95424026ed.stream-legacy.hg ec2region=us-west-2 stream=revlogv1
   https://s3-external-1.amazonaws.com/moz-hg-bundles-us-east-1/mozilla-central/4a7526d26bd47ce2e01f938702b91c95424026ed.stream-legacy.hg ec2region=us-east-1 stream=revlogv1

As you can see, listed bundle URLs vary by bundle type (compression and
format) and location. For each repository we generate bundles for, we
generate:

1. A gzip bundle (the default compression format)
2. A bzip2 bundle (smaller, but slower)
3. A *streaming* bundle file (larger but faster)

For each of these bundles, we upload them to 3 locations:

1. CloudFront CDN
2. S3 in us-west-2 region
3. S3 in us-east-1 region

The gzipped bundle hosted on CloudFront is the first entry and is thus
preferred by clients by default. **This is optimized for developers on
high speed network connections.**

If you have a slower internet connection, you may want to prefer bzip2
bundles. While they take several more minutes of CPU time to apply, this
could be cancelled out from the shorter time required to download them.
To prefer bzip2 bundles::

   # clone bundles config
   [experimental]
   clonebundleprefers = COMPRESSION=bzip2

   # bundleclone config
   [bundleclone]
   prefers = compression=bzip2

If you have a super fast internet connection, you can prefer the
*packed*/*streaming* bundles. This will transfer 30-40% more data on
average, but will require almost no CPU to apply. If you can fetch from
S3 or CloudFront at 1 Gbps speeds, you should be able to clone Firefox
in under 60s.::

   [experimental]
   clonebundleprefers = VERSION=packed1

   [bundleclone]
   prefers = stream=revlogv1

If you are in EC2, you should **always** pin your EC2 region as the
first entry. You should also prefer *stream bundle* mode, as network
bandwidth is plentiful and clones will be faster. e.g.::

   [experimental]
   clonebundleprefers = ec2region=us-west-2, VERSION=packed1

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
know by filing a ``Developer Services :: hg.mozilla.org`` bug or by
asking in #vcs on irc.mozilla.org.
