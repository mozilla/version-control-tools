# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

FROM secure:mozsecure:centos6:sha256 b102bf1f050742033c6255c6877283a0dcc169b40da3a0c96a630df440760c52:https://s3-us-west-2.amazonaws.com/moz-packages/docker-images/centos-6-20171101-docker.tar.xz

RUN yum update -y && yum install -y gcc libyaml-devel python-devel rsync tar && yum clean all

# Pin setuptools and pip because we've historically had issues with newer versions.
# Plus, pinning ensures reproducibility over time.
# %include scripts/download-verify
ADD extra/vct/scripts/download-verify /tmp/download-verify

RUN /tmp/download-verify https://s3-us-west-2.amazonaws.com/moz-packages/setuptools-20.1.1.tar.gz \
      /tmp/setuptools-20.1.1.tar.gz \
      2663ce0b0e742ee27c3a06b2da14563e4f6f713eaf5509b932a31793f9dea9a3 && \
    cd /tmp && tar -xzf setuptools-20.1.1.tar.gz && \
    cd /tmp/setuptools-20.1.1 && python setup.py install

RUN /tmp/download-verify https://s3-us-west-2.amazonaws.com/moz-packages/pip-8.0.3.tar.gz \
      /tmp/pip-8.0.3.tar.gz \
      30f98b66f3fe1069c529a491597d34a1c224a68640c82caf2ade5f88aa1405e8 && \
    cd /tmp && tar -xzf pip-8.0.3.tar.gz && \
    cd /tmp/pip-8.0.3 && python setup.py install

# Pinned to 1.9 because 2.0 is ~2x slower :/
# %include ansible/files/requirements-ansible-1.9.txt
ADD extra/vct/ansible/files/requirements-ansible-1.9.txt /tmp/
RUN pip install --require-hashes -r /tmp/requirements-ansible-1.9.txt
RUN mkdir /etc/ansible && echo -e '[local]\nlocalhost\n' > /etc/ansible/hosts
RUN mkdir /vct
ADD sync-and-build /sync-and-build
