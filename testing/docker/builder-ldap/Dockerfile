# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

# This is a Docker container for running a Mozilla flavored LDAP server.

FROM rockylinux:8

RUN yum update -y && yum install --enablerepo=powertools -y openldap-servers sudo && yum clean all

RUN rm -rf /etc/openldapldap/slapd.d

ADD testing/docker/builder-ldap/ldap.conf /etc/openldap/ldap.conf
ADD testing/docker/builder-ldap/slapd.conf /etc/openldap/slapd.conf
ADD testing/docker/builder-ldap/ssh_lpk.schema /etc/openldap/schema/ssh_lpk.schema
ADD testing/docker/builder-ldap/mozilla.schema /etc/openldap/schema/mozilla.schema
RUN chown -R ldap:ldap /etc/openldap

# Seed the data.
RUN mkdir /var/slapd
RUN chown ldap:ldap /var/slapd
ADD testing/docker/builder-ldap/mozilla.ldif /mozilla.ldif
RUN chown ldap:ldap /mozilla.ldif
RUN sudo -u ldap /usr/sbin/slapadd -v -f /etc/openldap/slapd.conf -l /mozilla.ldif

ADD testing/docker/builder-ldap/entrypoint.sh /entrypoint.sh

EXPOSE 389

ENTRYPOINT ["/entrypoint.sh"]
CMD ["/usr/sbin/slapd", "-h", "ldap:///", "-g", "ldap", "-u", "ldap", "-f", "/etc/openldap/slapd.conf", "-d", "256"]
