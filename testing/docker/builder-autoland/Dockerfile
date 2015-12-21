# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

# This is a Docker container for running an autoland instance

FROM secure:mozsecure:ubuntu14042:sha256 e08475e91c8b342dce147346a11db16357619ed914aaad4d82be2e6ab743a167:https://s3-us-west-2.amazonaws.com/moz-packages/docker-images/ubuntu-trusty-core-cloudimg-amd64-docker-20150630.tar.xz

ENV VCT_HOME /home/ubuntu/version-control-tools
ENV AUTOLAND_HOME /home/ubuntu/version-control-tools/autoland

RUN /usr/sbin/groupadd -g 1000 ubuntu
RUN /usr/sbin/useradd --no-create-home -u 1000 -g 1000 ubuntu

RUN apt-get update && apt-get --no-install-recommends -y install \
  apache2 curl gcc libapache2-mod-wsgi openssh-client postgresql-client \
  python2.7-dev python-pip libffi6 libffi-dev libpq-dev ca-certificates

# Python
# %include autoland/requirements.txt
ADD extra/vct/autoland/requirements.txt ${AUTOLAND_HOME}/requirements.txt

# TODO: We should install pip this way rather than through the python-pip
#       package, but this has failed consistently for a week.
#RUN curl -SL 'https://bootstrap.pypa.io/get-pip.py' | python2
RUN pip install virtualenv
RUN virtualenv ${AUTOLAND_HOME}/venv
RUN ${AUTOLAND_HOME}/venv/bin/pip install -r ${AUTOLAND_HOME}/requirements.txt

# Apache
RUN a2enmod headers
RUN rm /etc/apache2/sites-enabled/*
ADD autoland.conf /etc/apache2/sites-enabled/autoland.conf
EXPOSE 80

# Hg
RUN pip install Mercurial==3.6.2
RUN cd /home/ubuntu && hg clone -r 4140d680784e https://bitbucket.org/marmoute/mutable-history
RUN mkdir /repos && hg init /repos/try
ADD try-hgrc /repos/try/.hg/hgrc
ADD try_hook.sh /

# SSH
ADD ssh_config /root/.ssh/config
ADD autoland_id_rsa /root/.ssh/id_rsa
ADD autoland_id_rsa.pub /root/.ssh/id_rsa.pub
RUN chmod 600 -R /root/.ssh

#
ADD config.json ${AUTOLAND_HOME}/autoland/config.json
ADD clone-repo /clone-repo
ADD start-autoland.sh /start-autoland.sh
CMD ["/start-autoland.sh"]

# %include autoland/autoland/
# %include autoland/hgext/
# %include hgext/bootstrap.py
# %include hgext/reviewboard
# %include pylib/mozautomation
# %include pylib/mozhg
# %include run-tests
ADD extra/vct/autoland/autoland ${AUTOLAND_HOME}/autoland
ADD extra/vct/autoland/hgext ${AUTOLAND_HOME}/hgext
ADD extra/vct/run-tests ${VCT_HOME}/run-tests
ADD extra/vct/hgext/bootstrap.py ${VCT_HOME}/hgext/bootstrap.py
ADD extra/vct/hgext/reviewboard ${VCT_HOME}/hgext/reviewboard
ADD extra/vct/pylib/mozautomation ${VCT_HOME}/pylib/mozautomation
ADD extra/vct/pylib/mozhg ${VCT_HOME}/pylib/mozhg
