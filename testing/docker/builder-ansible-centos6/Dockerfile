# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

FROM centos:centos6

RUN yum update -y && yum install -y gcc libyaml-devel python-devel rsync && yum clean all
RUN curl https://bootstrap.pypa.io/get-pip.py | python
RUN pip install ansible
RUN mkdir /etc/ansible && echo -e '[local]\nlocalhost\n' > /etc/ansible/hosts
RUN mkdir /vct
ADD sync-and-build /sync-and-build
