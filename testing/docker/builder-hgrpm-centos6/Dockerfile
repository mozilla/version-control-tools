# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

# This is a Docker container for building Mercurial RPMs.

FROM secure:mozsecure:centos6:sha256 ce74b52232c2b4e3f88d54cc5ea1f91f93003f09bf79087b40eda774a58a887e:https://s3-us-west-2.amazonaws.com/moz-packages/docker-images/centos-6-20160818-docker.tar.xz

RUN yum install -y createrepo gcc gettext make mercurial python-devel python-docutils rpm-build tar

RUN hg clone https://selenic.com/repo/hg /hg
RUN mkdir /hg-packages

ENV HG_VERSIONS 3.7.3

ADD entrypoint.sh /entrypoint.sh
ADD rpmserver.py /rpmserver.py

ENTRYPOINT ["/entrypoint.sh"]
EXPOSE 80
CMD ["/usr/bin/python", "/rpmserver.py"]
