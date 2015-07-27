# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

# This is a Docker container for running a Mozilla flavored LDAP server.

FROM secure:mozsecure:ubuntu14042:sha256 e08475e91c8b342dce147346a11db16357619ed914aaad4d82be2e6ab743a167:https://s3-us-west-2.amazonaws.com/moz-packages/docker-images/ubuntu-trusty-core-cloudimg-amd64-docker-20150630.tar.xz

RUN apt-get update && apt-get --no-install-recommends -y install slapd

RUN rm -rf /etc/ldap/slapd.d

ADD ldap.conf /etc/ldap/ldap.conf
ADD slapd.conf /etc/ldap/slapd.conf
ADD ssh_lpk.schema /etc/ldap/schema/ssh_lpk.schema
ADD mozilla.schema /etc/ldap/schema/mozilla.schema
RUN chown -R openldap:openldap /etc/ldap

# Seed the data.
RUN mkdir /var/slapd
RUN chown openldap:openldap /var/slapd
ADD mozilla.ldif /mozilla.ldif
RUN sudo -u openldap /usr/sbin/slapadd -v -f /etc/ldap/slapd.conf -l /mozilla.ldif

ADD entrypoint.sh /entrypoint.sh

EXPOSE 389

ENTRYPOINT ["/entrypoint.sh"]
CMD ["/usr/sbin/slapd", "-h", "ldap:///", "-g", "openldap", "-u", "openldap", "-f", "/etc/ldap/slapd.conf", "-d", "256"]
