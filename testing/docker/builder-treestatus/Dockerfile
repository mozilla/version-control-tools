# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

# This is a Docker container for running a treestatus instance

FROM secure:mozsecure:ubuntu14042:sha256 e08475e91c8b342dce147346a11db16357619ed914aaad4d82be2e6ab743a167:https://s3-us-west-2.amazonaws.com/moz-packages/docker-images/ubuntu-trusty-core-cloudimg-amd64-docker-20150630.tar.xz

ENV TREESTATUS_HOME /home/ubuntu/treestatus

RUN /usr/sbin/groupadd -g 1000 ubuntu
RUN /usr/sbin/useradd --no-create-home -u 1000 -g 1000 ubuntu

RUN apt-get update && apt-get --no-install-recommends -y install \
  ca-certificates git python2.7-dev python-pip sqlite3

RUN git clone https://github.com/globau/treestatus-legacy.git ${TREESTATUS_HOME}

RUN pip install -r ${TREESTATUS_HOME}/requirements/compiled.txt

ADD testapp.py ${TREESTATUS_HOME}/testapp.py
ADD who.ini ${TREESTATUS_HOME}/who.ini
ADD htpasswd /htpasswd
CMD ["python", "/home/ubuntu/treestatus/testapp.py"]
EXPOSE 80
