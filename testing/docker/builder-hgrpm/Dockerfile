# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

# This is a Docker container for building Mercurial RPMs.

FROM secure:mozsecure:centos6:sha256 88cc1475bd58f6ff6f41d50b813c9998c4d3a7167a8a45f8bd0b4a8342dec0db:https://s3-us-west-2.amazonaws.com/moz-packages/docker-images/centos-6-20150615_2019-docker.tar.xz

RUN yum install -y createrepo gcc gettext make mercurial python-devel python-docutils rpm-build tar

RUN hg clone http://selenic.com/repo/hg /hg
RUN mkdir /hg-packages

ENV HG_VERSIONS 3.2.3 3.2.4 3.3.2

ADD entrypoint.sh /entrypoint.sh
ADD rpmserver.py /rpmserver.py

ENTRYPOINT ["/entrypoint.sh"]
EXPOSE 80
CMD ["/usr/bin/python", "/rpmserver.py"]
