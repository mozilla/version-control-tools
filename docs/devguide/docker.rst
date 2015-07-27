.. _devguide_docker:

======
Docker
======

Our development and test environment uses Docker extensively. The main
goal of Docker is to facilitate developing and testing code in an
environment that is as close to production as possible.

Image Management
================

We manage Docker images differently than most. We don't use Docker in
production (yet). But, we also want our Docker images to match the
server environment as closely as possible. If we were to use Dockerfiles
to maintain the Docker environment and something *not Docker* to manage
the servers, we would have duplication of effort and divergence between
Docker and production and this would undermine the effectiveness of the
Docker environment for mimicking production.

Instead of maintaining a Dockerfile for each image, we instead prefer to
maintain Dockerfiles for base, bare bones images configured with Ansible.
Then, we create and update Docker images by running an Ansible playbook
on this base image.

Secure Base Images
==================

Docker fails to take a secure approach to pulling images. For more, read
`Docker Insecurity <https://titanous.com/posts/docker-insecurity>`_.
We take security seriously, so we've added secure image pulling into
our Docker wrapper.

We introduce a special ``FROM`` syntax in Dockerfiles that initiates a
secure pull of that base image. The syntax is as follows::

   FROM secure:<repository>:<tag prefix>:<digest>:<URL>

e.g.::

   FROM secure:mozsecure:ubuntu14042:sha256 e08475e91c8b342dce147346a11db16357619ed914aaad4d82be2e6ab743a167:https://s3-us-west-2.amazonaws.com/moz-packages/docker-images/ubuntu-trusty-core-cloudimg-amd64-docker-20150630.tar.xz

When encountered, we will pull the image from the URL specified, verify
its digest matches what is defined, then import the image, and finally
associate it with the repository specified. The Dockerfile seen by
Docker is dynamically rewritten to reference the securely, just-imported
image.
