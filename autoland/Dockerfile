# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

# This is a Docker container for running an autoland instance

FROM ubuntu:14.04.1

ENV AUTOLAND_HOME /home/ubuntu/autoland

RUN /usr/sbin/groupadd -g 1000 ubuntu
RUN /usr/sbin/useradd --no-create-home -u 1000 -g 1000 ubuntu

RUN apt-get update && apt-get -y install \
  apache2 curl libapache2-mod-wsgi postgresql \
  python2.7-dev libpq-dev libldap2-dev libsasl2-dev \
  mercurial

# Python
ADD requirements.txt ${AUTOLAND_HOME}/requirements.txt
ADD autoland ${AUTOLAND_HOME}/autoland

RUN curl -SL 'https://bootstrap.pypa.io/get-pip.py' | python2
RUN pip install virtualenv
RUN virtualenv ${AUTOLAND_HOME}/venv
RUN ${AUTOLAND_HOME}/venv/bin/pip install -r ${AUTOLAND_HOME}/requirements.txt

# Apache
RUN a2enmod headers
RUN rm /etc/apache2/sites-enabled/*
ADD apache/autoland.conf /etc/apache2/sites-enabled/autoland.conf
EXPOSE 80

# Hg
RUN mkdir /repos && hg init /repos/mozilla-central && hg init /repos/try
RUN cd /repos/mozilla-central && hg bookmark central
ADD testing/docker/mozreview.tgz /repos
ADD testing/docker/hgrc /repos/mozilla-central/.hg/hgrc
ADD testing/docker/try-hgrc /repos/try/.hg/hgrc
ADD testing/docker/try_hook.sh /

#
ADD testing/docker/repo-config.json ${AUTOLAND_HOME}/autoland/repo-config.json 
ADD testing/docker/database-config.json ${AUTOLAND_HOME}/autoland/database-config.json 
ADD sql ${AUTOLAND_HOME}/sql
ADD testing/docker/start-autoland.sh ${AUTOLAND_HOME}/start-autoland.sh
CMD ${AUTOLAND_HOME}/start-autoland.sh
