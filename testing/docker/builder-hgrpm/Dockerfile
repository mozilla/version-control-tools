# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

# This is a Docker container for building Mercurial RPMs.

FROM centos:centos6

RUN yum install -y createrepo gcc gettext make mercurial python-devel python-docutils rpm-build tar

RUN hg clone http://selenic.com/repo/hg /hg
RUN mkdir /hg-packages

ENV HG_VERSIONS 3.2.3 3.2.4 3.3.2

ADD entrypoint.sh /entrypoint.sh
ADD rpmserver.py /rpmserver.py

ENTRYPOINT ["/entrypoint.sh"]
EXPOSE 80
CMD ["/usr/bin/python", "/rpmserver.py"]
