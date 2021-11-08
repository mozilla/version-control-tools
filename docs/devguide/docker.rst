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

