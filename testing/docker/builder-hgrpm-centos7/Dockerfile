# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

# This is a Docker container for building Mercurial RPMs.

FROM secure:mozsecure:centos7:sha256 874fae9bdbb7efd5c052d15330200184f71e36809157c2cf003c36df2eb467c7:https://s3-us-west-2.amazonaws.com/moz-packages/docker-images/centos-7-20160818-docker.tar.xz

RUN yum install -y createrepo gcc gettext make mercurial python-devel python-docutils rpm-build tar

RUN hg clone https://selenic.com/repo/hg /hg
RUN mkdir /hg-packages

ENV HG_VERSIONS 3.7.3

ADD entrypoint.sh /entrypoint.sh
ADD rpmserver.py /rpmserver.py

ENTRYPOINT ["/entrypoint.sh"]
EXPOSE 80
CMD ["/usr/bin/python", "/rpmserver.py"]
