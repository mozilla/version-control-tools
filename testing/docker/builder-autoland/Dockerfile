# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

# This is a Docker container for running an autoland instance

FROM ubuntu:14.04.2

ENV VCT_HOME /home/ubuntu/version-control-tools
ENV AUTOLAND_HOME /home/ubuntu/version-control-tools/autoland

RUN /usr/sbin/groupadd -g 1000 ubuntu
RUN /usr/sbin/useradd --no-create-home -u 1000 -g 1000 ubuntu

RUN apt-get update && apt-get --no-install-recommends -y install \
  apache2 curl gcc libapache2-mod-wsgi postgresql-client \
  python2.7-dev libffi6 libffi-dev libpq-dev libldap2-dev libsasl2-dev \
  mercurial ca-certificates

# Python
# %include autoland/requirements.txt
# %include autoland/autoland/
# %include pylib/mozautomation/mozautomation/
ADD extra/vct/autoland/requirements.txt ${AUTOLAND_HOME}/requirements.txt
ADD extra/vct/autoland/autoland ${AUTOLAND_HOME}/autoland
ADD extra/vct/pylib/mozautomation/mozautomation/ ${VCT_HOME}/pylib/mozautomation/

RUN curl -SL 'https://bootstrap.pypa.io/get-pip.py' | python2
RUN pip install virtualenv
RUN virtualenv ${AUTOLAND_HOME}/venv
RUN ${AUTOLAND_HOME}/venv/bin/pip install -r ${AUTOLAND_HOME}/requirements.txt

# Apache
RUN a2enmod headers
RUN rm /etc/apache2/sites-enabled/*
ADD autoland.conf /etc/apache2/sites-enabled/autoland.conf
EXPOSE 80

# Hg
RUN mkdir /repos && hg init /repos/mozilla-central && hg init /repos/try
RUN cd /repos/mozilla-central && hg bookmark central
ADD mozreview.tgz /repos
ADD hgrc /repos/mozilla-central/.hg/hgrc
ADD try-hgrc /repos/try/.hg/hgrc
ADD try_hook.sh /

#
ADD config.json ${AUTOLAND_HOME}/autoland/config.json
ADD start-autoland.sh /start-autoland.sh
CMD ["/start-autoland.sh"]
