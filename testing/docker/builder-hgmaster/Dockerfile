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
RUN yum install -y update; yum clean all
RUN yum install -y openssh-server git sudo; yum clean all
RUN yum localinstall -y http://people.mozilla.org/~bkero/mercurial-3.2.1+2-3246801ff313.x86_64.rpm

# TODO: Use the virtualenv instead of global package
#RUN yum -y install epel-release python-pip python-virtualenv gcc
#RUN mkdir /hg; cd /hg; virtualenv venv
#RUN cd /hg; source venv/bin/activate; pip install mercurial

# Add an example user for testing (guest/guest, member of scm_level_1)
RUN groupadd scm_level_1; groupadd scm_level_2; groupadd scm_level_3
RUN useradd guest; echo guest:guest|chpasswd; gpasswd -a guest scm_level_1
RUN mkdir -p /home/guest; chown guest:guest /home/guest

# Add the hg user
RUN useradd hg

# Set root password to something for debugging purposes
RUN echo root:mozillafirefox|chpasswd

# Set up Mercurial, adding example content
RUN mkdir -p /etc/mercurial
RUN mkdir -p /repo_local/mozilla/mozilla /repo_local/mozilla/extensions /repo_local/mozilla/scripts /repo
RUN ln -sf /repo_local/mozilla /repo/hg

# Clone the xforms repo as a small example repository
RUN hg clone -U https://hg.mozilla.org/xforms /repo/hg/mozilla/xforms; chmod -R 2775 /repo/hg/mozilla/xforms; chown -R hg:scm_level_1 /repo/hg/mozilla/xforms

# Set up users directories, make permissions right
RUN mkdir -p /repo_local/mozilla/mozilla/users
RUN chmod 2775 /repo_local/mozilla/mozilla/users
RUN chown -R hg:scm_level_1 /repo_local/mozilla/mozilla/users

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

# Put the files in the right place
ADD extra/vct/scripts/pash/* /usr/local/bin/

# TODO: Set up an LDAP container, run tests against it
# Comment out the ldap nastiness
RUN sed -i 's/, ldap_helper//; s/ .*ldap_helper.*/           pass/' /usr/local/bin/pash.py
RUN sed -i 's/^from ldap_helper.*//; s/    account_status =.*/    return 1/' /usr/local/bin/hg_helper.py

# Fix path in pash.py
RUN sed -i "s/'\/repo_local\/mozilla/'\/repo_local\/mozilla\/mozilla/" /usr/local/bin/hg_helper.py

# Configure sshd to use pash.py
RUN sed -i 's/#\tForceCommand.*/ForceCommand \/usr\/local\/bin\/pash.py/' /etc/ssh/sshd_config
RUN sed -i 's/#PermitRootLogin/PermitRootLogin/' /etc/ssh/sshd_config

# Generate the SSH host keys
RUN service sshd start


EXPOSE 22
CMD ["/usr/sbin/sshd", "-D"]
