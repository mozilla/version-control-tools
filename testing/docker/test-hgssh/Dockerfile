# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

FROM rockylinux:9

RUN yum update -y && \
    yum install --enablerepo=crb -y \
        gcc \
        libffi-devel \
        libyaml-devel \
        make \
        openssl-devel \
        python3-devel \
        python3-pip \
        rsync \
        tar && \
    yum clean all

ENV LC_ALL=C.UTF-8

RUN pip3 install --upgrade pip setuptools

COPY . /vct

RUN pip3 install --require-hashes -r /vct/ansible/files/requirements-ansible.txt
RUN mkdir /etc/ansible && echo -e '[local]\nlocalhost\n' > /etc/ansible/hosts

WORKDIR /vct/ansible
RUN ansible-playbook -c local test-hgmaster.yml
WORKDIR /vct
