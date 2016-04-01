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
# When running the container, the following environment variables can be
# set to influence behavior:
#
#   DB_NAME
#     The database to store Bugzilla data in.
#   DB_TIMEOUT
#     How long to wait for the database server to become available.
#   ADMIN_EMAIL
#     The email address to use for the admin account.
#   ADMIN_PASSWORD
#     The password to use for the admin account.
#   BMO_URL
#     The URL that Bugzilla will be exposed as. Bugzilla needs to
#     dynamically construct URLs during HTTP response generation. The
#     value of this environment variable will form the prefix for all
#     URLs.
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
#   docker run -e RESET_DATABASE=1 bmoweb
#
# Known Issues
# ============
#
# Our base image is Ubuntu. We should be using CentOS or Fedora for maximum
# compatibility with Mozilla's actual deployment.
#
# We hard-code use of MySQL. Bugzilla supports other database engines.
#
# We blow away the Bugzilla data directory during container start.

FROM secure:mozsecure:ubuntu14042:sha256 e08475e91c8b342dce147346a11db16357619ed914aaad4d82be2e6ab743a167:https://s3-us-west-2.amazonaws.com/moz-packages/docker-images/ubuntu-trusty-core-cloudimg-amd64-docker-20150630.tar.xz

ADD CLOBBER /CLOBBER

ENV BUGZILLA_HOME /var/lib/bugzilla
ENV DB_NAME bugs
ENV ADMIN_EMAIL admin@example.com
ENV ADMIN_PASSWORD password
ENV BMO_URL http://localhost:80/

RUN /usr/sbin/groupadd -g 1000 bugzilla
RUN /usr/sbin/useradd --no-create-home -u 1000 -g 1000 bugzilla

RUN apt-key adv --keyserver ha.pool.sks-keyservers.net --recv-keys A4A9406876FCBD3C456770C88C718D3B5072E1F5
RUN echo "deb http://repo.mysql.com/apt/ubuntu/ trusty mysql-5.6" > /etc/apt/sources.list.d/mysql.list

RUN apt-get update && apt-get --no-install-recommends -y install \
  apache2 build-essential cpanminus cvs g++ git graphviz \
  libapache2-mod-perl2 \
  libdaemon-generic-perl libfile-slurp-perl libdbd-mysql-perl \
  libgd-dev libssl-dev \
  mysql-client mysql-server \
  patchutils perlmagick pkg-config python3-mysql.connector \
  python-psutil supervisor unzip wget

RUN git clone --depth 1 https://git.mozilla.org/webtools/bmo/bugzilla.git $BUGZILLA_HOME/bugzilla

# cpanm has problems with some packages. Install them from the OS.
RUN apt-get -y install \
  libsoap-lite-perl \
  libmath-bigint-gmp-perl \
  libmath-mpfr-perl \
  libmath-prime-util-gmp-perl

RUN cd $BUGZILLA_HOME/bugzilla && ./checksetup.pl --cpanfile

# Linux::Pid is a dependency for Apache::SizeLimit that for whatever
# reason isn't detected by CPAN.
# XPLRPC::Transport::HTTP is needed by xmlrpc.cgi. For whatever reason,
# this dependency isn't installed.
RUN cd $BUGZILLA_HOME/bugzilla && cpanm Linux::Pid XMLRPC::Transport::HTTP
RUN cd $BUGZILLA_HOME/bugzilla && cpanm \
  --installdeps \
  --with-recommends \
  --with-all-features \
  --without-feature oracle --without-feature sqlite \
  --without-feature pg --without-feature elasticsearch \
  --notest \
  .

ADD checksetup_answers.txt $BUGZILLA_HOME/checksetup_answers.txt

# Configure MySQL
RUN rm -rf /var/lib/mysql
ADD my.cnf /etc/mysql/my.cnf
ADD mysql-init.sh /tmp/mysql-init.sh
RUN /usr/bin/mysql_install_db --user=mysql --datadir=/var/lib/mysql
RUN chown -R mysql:mysql /var/lib/mysql

# Configure Apache
RUN rm /etc/apache2/sites-enabled/*
RUN /usr/sbin/a2dismod mpm_event && /usr/sbin/a2enmod mpm_prefork
RUN /usr/sbin/a2enmod expires
RUN /usr/sbin/a2enmod headers
RUN /usr/sbin/a2enmod rewrite

ADD bugzilla.conf /etc/apache2/sites-enabled/25-bugzilla.conf
ADD prefork.conf /etc/apache2/mods-available/mpm_prefork.conf

ADD set-urls /set-urls
ADD entrypoint.py /bmoweb_entrypoint.py
ADD run-apache.sh /run-apache.sh

ADD supervisord.conf /etc/supervisor/conf.d/docker.conf

EXPOSE 80

ENTRYPOINT ["/bmoweb_entrypoint.py"]
CMD ["/usr/bin/supervisord"]
