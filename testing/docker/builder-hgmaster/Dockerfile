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

RUN curl https://mrepo.mozilla.org/mrepo/6Server-x86_64/RPMS.mozilla/openssh-lpk-5.4p1-1.x86_64.rpm > /openssh-lpk.rpm
RUN curl https://mrepo.mozilla.org/mrepo/6Server-x86_64/RPMS.mozilla/openssh-lpk-clients-5.4p1-1.x86_64.rpm > /openssh-lpk-clients.rpm
RUN curl https://mrepo.mozilla.org/mrepo/6Server-x86_64/RPMS.mozilla/openssh-lpk-server-5.4p1-1.x86_64.rpm > /openssh-lpk-server.rpm

RUN yum install -y authconfig nss-pam-ldapd openldap-clients pam_ldap python-ldap sudo syslog
RUN yum install -y /openssh-lpk.rpm /openssh-lpk-clients.rpm /openssh-lpk-server.rpm

RUN yum localinstall -y https://mrepo.mozilla.org/mrepo/6Server-x86_64/RPMS.mozilla/mercurial-3.3.2-0.x86_64.rpm

RUN yum clean all

# These should stay in sync with mozilla.ldif from the ldap server.
RUN groupadd -g 600 scm_level_1
RUN groupadd -g 601 scm_level_2
RUN groupadd -g 602 scm_level_3

# Add the hg user
RUN useradd hg

# Set root password to something for debugging purposes
RUN echo root:mozillafirefox|chpasswd

# Set up Mercurial, adding example content
RUN mkdir -p /etc/mercurial
RUN mkdir -p /repo/hg/mozilla /repo/hg/extensions /repo/hg/scripts

# Set up users directories, make permissions right
RUN mkdir -p /repo/hg/mozilla/users
RUN chmod 2775 /repo/hg/mozilla/users
RUN chown -R hg:scm_level_1 /repo/hg/mozilla/users

# Install Mercurial config files
ADD extra/vct/testing/docker/builder-hgmaster/hgrc /etc/mercurial/hgrc

# TODO: Write up the client and re-enable the mirror push script
RUN sed -i 's/changegroup.mirrorpush/#changegroup.mirrorpush/' /etc/mercurial/hgrc

# Copy scripts into place
ADD extra/vct/hgext/pushlog-legacy/* /repo/hg/extensions/
ADD extra/vct/hgext/serverlog /repo/hg/extensions/
ADD extra/vct/hghooks /repo/hg/libraries/
ADD extra/vct/scripts/record-pushes.sh /repo/hg/scripts/
ADD extra/vct/scripts/push-repo.sh /repo/hg/scripts/
ADD extra/vct/scripts/repo-push.sh /usr/local/bin/

# TODO: Fix this logging or remove record-pushes script as it's information duplicates serverlog
RUN touch /var/log/hg-push.log; chmod 666 /var/log/hg-push.log

RUN touch /var/log/pash.log && chmod 666 /var/log/pash.log

# Put the files in the right place
ADD extra/vct/scripts/pash/* /usr/local/bin/

ADD sshd_config /etc/ssh/sshd_config
ADD nslcd.conf /etc/nslcd.conf

RUN ssh-keygen -b 2048 -f /etc/mercurial/mirror -t rsa
RUN mkdir /home/hg/.ssh
RUN cp /etc/mercurial/mirror.pub /home/hg/.ssh/authorized_keys
RUN chown -R hg:hg /home/hg/.ssh
RUN chmod 640 /home/hg/.ssh/authorized_keys

ADD set-mirrors.py /set-mirrors.py
ADD entrypoint.py /entrypoint.py

EXPOSE 22

ENTRYPOINT ["/entrypoint.py"]
CMD ["/usr/sbin/sshd", "-D"]
