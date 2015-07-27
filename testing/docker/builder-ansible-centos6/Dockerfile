# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

FROM secure:mozsecure:centos6:sha256 88cc1475bd58f6ff6f41d50b813c9998c4d3a7167a8a45f8bd0b4a8342dec0db:https://s3-us-west-2.amazonaws.com/moz-packages/docker-images/centos-6-20150615_2019-docker.tar.xz

RUN yum update -y && yum install -y gcc libyaml-devel python-devel rsync && yum clean all
RUN curl https://bootstrap.pypa.io/get-pip.py | python
# peep does not yet work with pip 7. Also, setuptools had a few releases
# where they broke imp module importing. Pin to old, known working,
# versions.
RUN pip install -U pip==6.0.8 setuptools==15.2
RUN pip install ansible
RUN mkdir /etc/ansible && echo -e '[local]\nlocalhost\n' > /etc/ansible/hosts
RUN mkdir /vct
ADD sync-and-build /sync-and-build
