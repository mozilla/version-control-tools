# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

# This container holds a copy of all vct data.

FROM secure:mozsecure:centos7:sha256 219b47fc575d9884a7062a575ca36e71b03f14ebfbb5a87f41ae8475b925e903:https://s3-us-west-2.amazonaws.com/moz-packages/docker-images/centos-7-20170515-docker.tar.xz

RUN yum update -y && yum install -y rsync && yum clean all

VOLUME /vct-mount
ADD run.sh /run.sh

CMD ["/run.sh"]
