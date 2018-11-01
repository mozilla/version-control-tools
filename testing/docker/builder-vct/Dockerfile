# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

# This container holds a copy of all vct data.

FROM secure:mozsecure:centos7:sha256 48cc2d545136115b38f38ee5f80d51db391fee2610f8300b280b35422db63af7:https://s3-us-west-2.amazonaws.com/moz-packages/docker-images/centos-7-20181101-docker.tar.xz

RUN yum update -y && yum install -y rsync && yum clean all

VOLUME /vct-mount
ADD run.sh /run.sh

CMD ["/run.sh"]
