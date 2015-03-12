# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

# This Dockerfile creates a docker container for running a Mercurial server
# that is ideally indistinguishable from the production hg.mozilla.org SSH
# server. It installs Mercurial, adds some users and groups, and scripts
# that mirror production (or what production will be). Should accompany
# the hgweb-slave script.

FROM centos:centos6

RUN yum update -y && yum install -y gcc libyaml-devel python-devel && yum clean all
RUN curl https://bootstrap.pypa.io/get-pip.py | python
RUN pip install ansible

RUN mkdir /etc/ansible && echo '[local]\nlocalhost\n' > /etc/ansible/hosts

# %include ansible/
ADD extra/vct/ansible/ /ansible

RUN cd /ansible && python -u /usr/bin/ansible-playbook docker-hgmaster.yml -c local

# %include scripts/pash/
# %include hgext/pushlog-legacy/
# %include hgext/pushlog/
# %include hgext/serverlog/
# %include hghooks/
# %include scripts/
ADD extra/vct/scripts/pash/* extra/vct/scripts/repo-push.sh /usr/local/bin/
ADD extra/vct/hgext/pushlog-legacy/buglink.py extra/vct/hgext/pushlog-legacy/feedparser.py extra/vct/hgext/pushlog-legacy/hgwebjson.py extra/vct/hgext/pushlog-legacy/pushlog-feed.py /repo/hg/extensions/
ADD extra/vct/hgext/pushlog-legacy/parsedatetime/* /repo/hg/extensions/parsedatetime/
ADD extra/vct/hgext/pushlog/* /repo/hg/extensions/pushlog/
ADD extra/vct/hgext/serverlog/* /repo/hg/extensions/serverlog/
ADD extra/vct/hghooks /repo/hg/libraries/
ADD extra/vct/scripts/record-pushes.sh extra/vct/scripts/push-repo.sh /repo/hg/scripts/

ADD entrypoint.py /entrypoint.py

EXPOSE 22

ENTRYPOINT ["/entrypoint.py"]
CMD ["/usr/sbin/sshd", "-D"]
