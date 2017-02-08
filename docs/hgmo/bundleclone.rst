.. _hgmo_bundleclone:

==================================
Cloning from Pre-Generated Bundles
==================================

``hg.mozilla.org`` supports offloading clone requests to pre-generated
bundle files stored in a CDN and Amazon S3. **This results in drastically
reduced server load (which helps prevent outages due to accidental,
excessive load) and frequently results in faster clone times.**

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

If you are running Mercurial 3.7 or newer, support for cloning from
pre-generated bundles is built-in to Mercurial itself and enabled
by default.

If you are running Mercurial 3.6, support is built-in but requires
enabling a config option::

   [experimental]
   clonebundles = true

If you are running a Mercurial older than 3.6, upgrade to leverage the
clone bundles feature.

Configuring
===========

hg.mozilla.org will advertise multiple bundles/URLs for each repository.
Each listing varies by:

* Bundle type
* Server location

By default, Mercurial uses the first entry in the server-advertised
bundles list.

The *clone bundles* feature allows the client to define preferences of
which bundles to fetch. The way this works is the client defines some
key-value pairs in its config and bundles having these attributes will
be upweighted.

Bundle Attributes on hg.mozilla.org
-----------------------------------

On ``hg.mozilla.org``, following attributes are defined in the manifest:

BUNDLESPEC
   This defines the type of bundle.

   We currently generate bundles with the following specifications:
   ``gzip-v1``, ``bzip2-v1``, ``none-packed1``.

REQUIRESNI
   Indicates whether the URL requires SNI (a TLS extension). This is set
   to ``true`` for URLs where multiple certificates are installed on the
   same IP and SNI is required. It is undefined if SNI is not required.

ec2region
   The EC2 region the bundle file should be served from. We support
   ``us-west-2`` and ``us-east-1``. You should prefer the region that is
   closest to you.

cdn
   Indicates whether the URL is on a CDN. Value is ``true`` to indicate
   the URL is a CDN. All other values or undefined values are to be
   interpretted as not a CDN.

Example Manifests
-----------------

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

Which Bundles to Prefer
-----------------------

The gzipped bundle hosted on CloudFront is the first entry and is thus
preferred by clients by default. **This is optimized for developers on
high speed network connections.**

If you have a slower internet connection, you may want to prefer bzip2
bundles. While they take several more minutes of CPU time to apply, this
could be cancelled out from the shorter time required to download them.
To prefer bzip2 bundles::

   # clone bundles config (3.7+)
   [ui]
   clonebundleprefers = COMPRESSION=bzip2

   # clone bundles config (3.6)
   [experimental]
   clonebundleprefers = COMPRESSION=bzip2

If you have a super fast internet connection, you can prefer the
*packed*/*streaming* bundles. This will transfer 30-40% more data on
average, but will require almost no CPU to apply. If you can fetch from
S3 or CloudFront at 1 Gbps speeds, you should be able to clone Firefox
in under 60s.::

   # HG 3.7+
   [ui]
   clonebundleprefers = VERSION=packed1

   # HG 3.6
   [experimental]
   clonebundleprefers = VERSION=packed1

Manifest Advertisement to AWS Clients
-------------------------------------

If a client in Amazon Web Services (e.g. EC2) is requesting a bundle
manifest and that client is in an AWS region where bundles are hosted
in S3, the advertised manifest will only show S3 URLs for the same AWS
region. In addition, stream clone bundles are the highest priority bundle.

This behavior ensures that AWS transfer are intra-region (which means
they are fast and don't result in a billable AWS event) and that ``hg
clone`` completes as fast as possible (stream clone bundles are faster
than gzip bundles).

.. important::

   If you have machinery in an AWS region where we don't host bundles,
   please let us know. There's a good chance that establishing bundles
   in your region is cheaper than paying the cross-region transfer costs
   (intra-region transfer is free).

Which Repositories Have Bundles Available
=========================================

Bundles are automatically generated for repositories that are high
volume (in terms of repository size and clone frequency) or have a need
for bundles.

The list of repositories with bundles enabled can be found at
https://hg.cdn.mozilla.net/. A JSON document describing the
bundles is available at https://hg.cdn.mozilla.net/bundles.json.

If you think bundles should be made available for a particular
repository, let a server operator know by filing a
``Developer Services :: hg.mozilla.org`` bug or by asking in #vcs
on irc.mozilla.org.
