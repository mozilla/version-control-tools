# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

# This container holds a copy of all vct data.

FROM secure:mozsecure:centos7:sha256 9f2f77ffd1614d29e5cc403c677eb726ede859f78e16017d608593cbbc3f0d2e:https://s3-us-west-2.amazonaws.com/moz-packages/docker-images/centos-7-20171101-docker.tar.xz

RUN yum update -y && yum install -y rsync && yum clean all

VOLUME /vct-mount
ADD run.sh /run.sh

CMD ["/run.sh"]
