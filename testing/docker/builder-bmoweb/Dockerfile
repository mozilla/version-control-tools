# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

# This is a Docker container for running an HTTP server that behaves
# like https://bugzilla.mozilla.org/.
#
# Building
# ========
#
# The container can be built by running:
#
#   docker build .
#
# You'll likely want to tag the image for easy reuse:
#
#   docker build -t bmoweb .
#
# The container takes a long time to build. The two long poles are
# installing the numerous required system packages and CPAN packages
# required by Bugzilla. Run time can balloon significantly if you are on
# a slow internet connection. Build times of 10 minutes on modern
# machines are expected.
#
# Running
# =======
#
# The container requires a link to a container running a MySQL database
# linked to this container with the name "bmodb". That container should
# be exposing MySQL on port 3306.
#
# Assuming a MySQL server is running in the "bmodb" container and you
# wish to expose the HTTP server on port 8000 of the current machine,
# start a container by running:
#
#   docker run -d --link bmodb:bmodb -p 8000:80 bmoweb
#
# This first time you do this, you may wish to run interactively to
# verify everything is working:
#
#   docker run -it --link bmodb:bmodb bmoweb
#
# You should then be able to open http://localhost:8000/ and log into
# Bugzilla using the admin credentials. The default username and
# password is: admin@example.com / password
#
# If you want an interactive shell in the container, provide a command
# to use to override the container's default (which runs Apache):
#
#   docker run -it --link bmodb:bmodb bmoweb /bin/bash
#
# When running the container, the following environment variables can be
# set to influence behavior:
#
#   DB_USER
#     The username to use when connecting to MySQL.
#   DB_PASS
#     The password to use when connecting to MySQL.
#   DB_NAME
#     The database to store Bugzilla data in.
#   ADMIN_EMAIL
#     The email address to use for the admin account.
#   ADMIN_PASSWORD
#     The password to use for the admin account.
#   RESET_DATABASE
#     If set, the MySQL database will be dropped when the container starts.
#     Typically, the bmodb container will have persistent data and
#     restarts of this bmoweb container will inherit database data from
#     the last run.
#
# The defaults are set to work with the bmodb builder from the builder-bmodb
# sibling directory.
#
# For example:
#
#   docker run --link bmodb:bmodb -e RESET_DATABASE=1 bmoweb
#
# Known Issues
# ============
#
# Our base image is Ubuntu. We should be using CentOS or Fedora for maximum
# compatibility with Mozilla's actual deployment.
#
# We hard-code use of MySQL. Bugzilla supports other database engines.
#
# The Git clone is never updated after container build. Fixing this
# requires dealing with the Bugzilla patching more elegantly.
#
# There is no control over which Git commit to use.
#
# We blow away the Bugzilla data directory during container start.

FROM ubuntu:14.04.1

ENV BUGZILLA_HOME /var/lib/bugzilla
ENV DB_USER root
ENV DB_PASS password
ENV DB_NAME bugs
ENV ADMIN_EMAIL admin@example.com
ENV ADMIN_PASSWORD password

RUN /usr/sbin/groupadd -g 1000 bugzilla
RUN /usr/sbin/useradd --no-create-home -u 1000 -g 1000 bugzilla

RUN apt-get update
RUN apt-get -y install apache2 build-essential cvs g++ git graphviz \
  libapache2-mod-perl2 libdaemon-generic-perl libgd-dev libssl-dev \
  mysql-client patchutils perlmagick pkg-config unzip

RUN git clone https://git.mozilla.org/webtools/bmo/bugzilla.git $BUGZILLA_HOME/bugzilla

# ElasticSearch isn't available on CPAN. Patch Bugzilla to not install
# it.
ADD elasticsearch.patch /elasticsearch.patch
RUN cd $BUGZILLA_HOME/bugzilla && /usr/bin/patch -p1 < /elasticsearch.patch

# Linux::Pid is a dependency for Apache::SizeLimit that for whatever
# reason isn't detected by CPAN.
# XPLRPC::Transport::HTTP is needed by xmlrpc.cgi. For whatever reason,
# this dependency isn't installed.
RUN cd $BUGZILLA_HOME/bugzilla && ./install-module.pl Linux::Pid XMLRPC::Transport::HTTP
RUN cd $BUGZILLA_HOME/bugzilla && ./install-module.pl --all

ADD checksetup_answers.txt $BUGZILLA_HOME/checksetup_answers.txt

# The .htaccess isn't compatible with Apache 2.4. We fix that.
ADD apache24.patch $BUGZILLA_HOME/apache24.patch
RUN cd $BUGZILLA_HOME/bugzilla && /usr/bin/patch -p1 < $BUGZILLA_HOME/apache24.patch

# Bug 769829. Foreign key issue with component watching schema updating.
ADD fkpatch.patch $BUGZILLA_HOME/fkpatch.patch
RUN cd $BUGZILLA_HOME/bugzilla && /usr/bin/patch -p1 < $BUGZILLA_HOME/fkpatch.patch

# Configure Apache
RUN rm /etc/apache2/sites-enabled/*
RUN /usr/sbin/a2dismod mpm_event && /usr/sbin/a2enmod mpm_prefork
RUN /usr/sbin/a2enmod expires
RUN /usr/sbin/a2enmod headers
RUN /usr/sbin/a2enmod rewrite

ADD bugzilla.conf /etc/apache2/sites-enabled/25-bugzilla.conf

ADD entrypoint.py /bmoweb_entrypoint.py
ADD run-apache.sh /run-apache.sh

EXPOSE 80

ENTRYPOINT ["/bmoweb_entrypoint.py"]
CMD ["/run-apache.sh"]
