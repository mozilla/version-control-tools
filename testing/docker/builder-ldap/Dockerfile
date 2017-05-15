# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

# This is a Docker container for running a Mozilla flavored LDAP server.

FROM secure:mozsecure:centos7:sha256 219b47fc575d9884a7062a575ca36e71b03f14ebfbb5a87f41ae8475b925e903:https://s3-us-west-2.amazonaws.com/moz-packages/docker-images/centos-7-20170515-docker.tar.xz

RUN yum update -y && yum install -y openldap-servers sudo && yum clean all

RUN rm -rf /etc/openldapldap/slapd.d

ADD ldap.conf /etc/openldap/ldap.conf
ADD slapd.conf /etc/openldap/slapd.conf
ADD ssh_lpk.schema /etc/openldap/schema/ssh_lpk.schema
ADD mozilla.schema /etc/openldap/schema/mozilla.schema
RUN chown -R ldap:ldap /etc/openldap

# Seed the data.
RUN mkdir /var/slapd
RUN chown ldap:ldap /var/slapd
ADD mozilla.ldif /mozilla.ldif
RUN chown ldap:ldap /mozilla.ldif
RUN sudo -u ldap /usr/sbin/slapadd -v -f /etc/openldap/slapd.conf -l /mozilla.ldif

ADD entrypoint.sh /entrypoint.sh

EXPOSE 389

ENTRYPOINT ["/entrypoint.sh"]
CMD ["/usr/sbin/slapd", "-h", "ldap:///", "-g", "ldap", "-u", "ldap", "-f", "/etc/openldap/slapd.conf", "-d", "256"]
