# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

# This is a Docker container for running a Review Board HTTP server.

FROM ubuntu:14.04.1

ENV RB_HOME /var/lib/reviewboard
ENV RB_VERSION 2.0.12

RUN /usr/sbin/groupadd -g 1000 reviewboard
RUN /usr/sbin/useradd --no-create-home -u 1000 -g 1000 reviewboard

RUN apt-get update && apt-get -y install \
  apache2 curl libapache2-mod-wsgi libmysqlclient-dev libxslt1-dev \
  mysql-client nodejs node-uglify npm \
  python2.7-dev python3-mysql.connector

# Needed to make some Node and RBMozUI packaging happy, sadly.
RUN ln -s /usr/bin/nodejs /usr/local/bin/node

# NPM package required for building Review Board extensions.
RUN npm install -g less

# Install pip and virtualenv from upstream because system packaging is teh suck.
RUN curl -SL 'https://bootstrap.pypa.io/get-pip.py' | python2
RUN pip install virtualenv

RUN mkdir -p /var/lib/reviewboard

RUN virtualenv ${RB_HOME}/venv
ADD extra/vct/test-requirements.txt ${RB_HOME}/requirements.txt
RUN ${RB_HOME}/venv/bin/pip install MySQL-python==1.2.5
RUN ${RB_HOME}/venv/bin/pip install -r ${RB_HOME}/requirements.txt
RUN ${RB_HOME}/venv/bin/easy_install ReviewBoard==${RB_VERSION}

RUN rm /etc/apache2/sites-enabled/*
ADD vhost.conf /etc/apache2/sites-enabled/reviewboard.conf

ADD entrypoint.py /entrypoint.py

ADD extra/vct/pylib/rbbz ${RB_HOME}/rbbz
ADD extra/vct/pylib/rbmozui ${RB_HOME}/rbmozui

RUN cd ${RB_HOME}/rbbz && ${RB_HOME}/venv/bin/python setup.py install
RUN cd ${RB_HOME}/rbmozui && ${RB_HOME}/venv/bin/python setup.py install

EXPOSE 80

ENTRYPOINT ["/entrypoint.py"]
CMD ["/usr/sbin/apache2ctl", "-D", "FOREGROUND"]
