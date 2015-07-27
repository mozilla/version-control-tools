# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

FROM secure:mozsecure:ubuntu14042:sha256 e08475e91c8b342dce147346a11db16357619ed914aaad4d82be2e6ab743a167:https://s3-us-west-2.amazonaws.com/moz-packages/docker-images/ubuntu-trusty-core-cloudimg-amd64-docker-20150630.tar.xz

RUN apt-get update && apt-get install -y curl gcc libyaml-dev python-dev rsync && apt-get clean
RUN curl https://bootstrap.pypa.io/get-pip.py | python2.7
RUN pip install ansible
RUN ln -s /usr/local/bin/ansible /usr/bin/ansible && ln -s /usr/local/bin/ansible-playbook /usr/bin/ansible-playbook
RUN mkdir /etc/ansible && /bin/echo -e '[local]\nlocalhost\n' > /etc/ansible/hosts
RUN mkdir /vct
ADD sync-and-build /sync-and-build
