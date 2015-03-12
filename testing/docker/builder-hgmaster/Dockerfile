# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

# This Dockerfile creates a docker container for running a Mercurial server
# that is ideally indistinguishable from the production hg.mozilla.org SSH
# server. It installs Mercurial, adds some users and groups, and scripts
# that mirror production (or what production will be). Should accompany
# the hgweb-slave script.

FROM centos:centos6
MAINTAINER Ben Kero <bkero@mozilla.com>

# Install requisite packages
RUN yum update -y

RUN yum install -y \
    authconfig \
    nss-pam-ldapd \
    openldap-clients \
    pam_ldap \
    python-devel \
    python-ldap \
    sudo \
    syslog \
    tar

# These are copies from Mozilla's internal "mrepo" repository.
RUN yum install -y \
    https://people.mozilla.org/~gszorc/openssh-lpk-5.4p1-1.x86_64.rpm \
    https://people.mozilla.org/~gszorc/openssh-lpk-clients-5.4p1-1.x86_64.rpm \
    https://people.mozilla.org/~gszorc/openssh-lpk-server-5.4p1-1.x86_64.rpm \
    https://people.mozilla.org/~gszorc/mercurial-3.3.2-0.x86_64.rpm

RUN yum clean all

RUN curl https://bootstrap.pypa.io/get-pip.py | python
RUN pip install coverage

# Docker doesn't have full TTYs. sudo will fail unless we disable this
# requirement.
RUN sed -i "s/Defaults    requiretty.*/#Defaults requiretty/g" /etc/sudoers

# These should stay in sync with mozilla.ldif from the ldap server.
RUN groupadd -g 600 scm_level_1 && groupadd -g 601 scm_level_2 && groupadd -g 602 scm_level_3

# Add the hg user
RUN useradd hg

# Set root password to something for debugging purposes
RUN echo root:mozillafirefox|chpasswd

RUN mkdir /coverage && chmod 777 /coverage

# Set up Mercurial, adding example content
RUN mkdir -p /etc/mercurial
RUN mkdir -p /repo/hg/mozilla /repo/hg/extensions /repo/hg/scripts

# Set up users directories, make permissions right
RUN mkdir -p /repo/hg/mozilla/users
RUN chmod 2775 /repo/hg/mozilla/users && chown -R hg:scm_level_1 /repo/hg/mozilla/users

RUN touch /etc/mercurial/known_hosts && chown hg /etc/mercurial/known_hosts

# TODO: Fix this logging or remove record-pushes script as it's information duplicates serverlog
RUN touch /var/log/hg-push.log && chmod 666 /var/log/hg-push.log

RUN touch /var/log/pash.log && chmod 666 /var/log/pash.log

ADD sshd_config /etc/ssh/sshd_config
ADD nslcd.conf /etc/nslcd.conf

RUN ssh-keygen -b 2048 -f /etc/mercurial/mirror -t rsa && chown hg /etc/mercurial/mirror /etc/mercurial/mirror.pub
RUN mkdir /home/hg/.ssh
RUN cp /etc/mercurial/mirror.pub /home/hg/.ssh/authorized_keys
RUN chown -R hg:hg /home/hg/.ssh
RUN chmod 640 /home/hg/.ssh/authorized_keys

ADD sitecustomize.py /usr/lib/python2.6/site-packages/sitecustomize.py
ADD repo-push.sudoers /etc/sudoers.d/repo-push
ADD create-repo set-mirrors.py entrypoint.py /
ADD hgrc /etc/mercurial/hgrc
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

EXPOSE 22

ENTRYPOINT ["/entrypoint.py"]
CMD ["/usr/sbin/sshd", "-D"]
