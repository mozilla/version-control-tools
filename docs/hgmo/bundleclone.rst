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

Mercurial 4.1 is required to support zstd bundles, which are smaller
and faster than bundles supported by earlier versions.

Configuring
===========

hg.mozilla.org will advertise multiple bundles/URLs for each repository.
Each listing varies by:

* Bundle type
* Server location

By default, Mercurial uses the first entry in the server-advertised
bundles list that the client supports.

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
   ``zstd-v2``, ``gzip-v1``, ``gzip-v2``, ``none-packed1``.

REQUIRESNI
   Indicates whether the URL requires SNI (a TLS extension). This is set
   to ``true`` for URLs where multiple certificates are installed on the
   same IP and SNI is required. It is undefined if SNI is not required.

ec2region
   The EC2 region the bundle file should be served from. We support
   ``us-west-1``, ``us-west-2``, ``us-east-1``, ``eu-central-``.
   You should prefer the region that is closest to you.

cdn
   Indicates whether the URL is on a CDN. Value is ``true`` to indicate
   the URL is a CDN. All other values or undefined values are to be
   interpretted as not a CDN.

Example Manifests
-----------------

Here is an example *clone bundles* manifest::

   https://hg.cdn.mozilla.net/mozilla-unified/82c75fd3a2de796351296592c459ab4aa4cd0baf.zstd-max.hg BUNDLESPEC=zstd-v2 REQUIRESNI=true cdn=true
   https://s3-us-west-2.amazonaws.com/moz-hg-bundles-us-west-2/mozilla-unified/82c75fd3a2de796351296592c459ab4aa4cd0baf.zstd-max.hg BUNDLESPEC=zstd-v2 ec2region=us-west-2
   https://s3-us-west-1.amazonaws.com/moz-hg-bundles-us-west-1/mozilla-unified/82c75fd3a2de796351296592c459ab4aa4cd0baf.zstd-max.hg BUNDLESPEC=zstd-v2 ec2region=us-west-1
   https://s3-external-1.amazonaws.com/moz-hg-bundles-us-east-1/mozilla-unified/82c75fd3a2de796351296592c459ab4aa4cd0baf.zstd-max.hg BUNDLESPEC=zstd-v2 ec2region=us-east-1
   https://s3-eu-central-1.amazonaws.com/moz-hg-bundles-eu-central-1/mozilla-unified/82c75fd3a2de796351296592c459ab4aa4cd0baf.zstd-max.hg BUNDLESPEC=zstd-v2 ec2region=eu-central-1
   https://hg.cdn.mozilla.net/mozilla-unified/82c75fd3a2de796351296592c459ab4aa4cd0baf.gzip-v2.hg BUNDLESPEC=gzip-v2 REQUIRESNI=true cdn=true
   https://s3-us-west-2.amazonaws.com/moz-hg-bundles-us-west-2/mozilla-unified/82c75fd3a2de796351296592c459ab4aa4cd0baf.gzip-v2.hg BUNDLESPEC=gzip-v2 ec2region=us-west-2
   https://s3-us-west-1.amazonaws.com/moz-hg-bundles-us-west-1/mozilla-unified/82c75fd3a2de796351296592c459ab4aa4cd0baf.gzip-v2.hg BUNDLESPEC=gzip-v2 ec2region=us-west-1
   https://s3-external-1.amazonaws.com/moz-hg-bundles-us-east-1/mozilla-unified/82c75fd3a2de796351296592c459ab4aa4cd0baf.gzip-v2.hg BUNDLESPEC=gzip-v2 ec2region=us-east-1
   https://s3-eu-central-1.amazonaws.com/moz-hg-bundles-eu-central-1/mozilla-unified/82c75fd3a2de796351296592c459ab4aa4cd0baf.gzip-v2.hg BUNDLESPEC=gzip-v2 ec2region=eu-central-1
   https://hg.cdn.mozilla.net/mozilla-unified/82c75fd3a2de796351296592c459ab4aa4cd0baf.packed1-gd.hg BUNDLESPEC=none-packed1;requirements%3Dgeneraldelta%2Crevlogv1 REQUIRESNI=true cdn=true
   https://s3-us-west-2.amazonaws.com/moz-hg-bundles-us-west-2/mozilla-unified/82c75fd3a2de796351296592c459ab4aa4cd0baf.packed1-gd.hg BUNDLESPEC=none-packed1;requirements%3Dgeneraldelta%2Crevlogv1 ec2region=us-west-2
   https://s3-us-west-1.amazonaws.com/moz-hg-bundles-us-west-1/mozilla-unified/82c75fd3a2de796351296592c459ab4aa4cd0baf.packed1-gd.hg BUNDLESPEC=none-packed1;requirements%3Dgeneraldelta%2Crevlogv1 ec2region=us-west-1
   https://s3-external-1.amazonaws.com/moz-hg-bundles-us-east-1/mozilla-unified/82c75fd3a2de796351296592c459ab4aa4cd0baf.packed1-gd.hg BUNDLESPEC=none-packed1;requirements%3Dgeneraldelta%2Crevlogv1 ec2region=us-east-1
   https://s3-eu-central-1.amazonaws.com/moz-hg-bundles-eu-central-1/mozilla-unified/82c75fd3a2de796351296592c459ab4aa4cd0baf.packed1-gd.hg BUNDLESPEC=none-packed1;requirements%3Dgeneraldelta%2Crevlogv1 ec2region=eu-central-1

As you can see, listed bundle URLs vary by bundle type (compression and
format) and location. For each repository we generate bundles for, we
generate:

1. A zstd bundle (either default compression or maximum compression depending
   on repo utilization)
2. A gzip bundle (the default compression format)
3. A *streaming* bundle file (larger but faster)

For each of these bundles, we upload them to the following locations:

1. CloudFront CDN
2. S3 in us-west-2 region
3. S3 in us-west-1 region
4. S3 in us-east-1 region
5. S3 in eu-central-1 region

Which Bundles to Prefer
-----------------------

The zstd bundle hosted on CloudFront is the first entry and is thus
preferred by clients by default.

zstd bundles are the smallest bundles and for most people they are
the ideal bundle to use.

.. note::

   Mercurial 4.1 is required to use zstd bundles. If an older Mercurial
   client is used, larger, non-zstd bundles will be used.

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

Manifest Advertisements to Mozilla Offices
------------------------------------------

If the client request appears to originate from a Mozilla office network,
we make the assumption that the network speed and bandwidth are sufficient
to always prefer the high-speed streamed clone bundles. 

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
