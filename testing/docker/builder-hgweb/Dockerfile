# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

FROM centos:centos6

RUN useradd -u 500 hg

RUN yum update -y

RUN mkdir -p /repo_local/mozilla/mozilla /repo
RUN ln -sf /repo_local/mozilla /repo/hg
RUN chown -R hg:hg /repo_local/mozilla/mozilla

RUN yum install -y httpd lockfile-progs mod_wsgi openssh-clients openssh-server \
    python-pygments python-simplejson python-argparse syslog

RUN yum install -y https://people.mozilla.org/~gszorc/mercurial-3.3.2-0.x86_64.rpm

RUN yum clean all

RUN hg clone http://hg.mozilla.org/hgcustom/library_overrides /repo_local/mozilla/library_overrides

ADD httpd.conf /etc/httpd/conf/httpd.conf
ADD vhost.conf /etc/httpd/conf.d/hg-vhost.conf
ADD mod_wsgi.conf /etc/httpd/conf.d/wsgi.conf
RUN mkdir /var/log/httpd/hg

ADD hgrc /etc/mercurial/hgrc
ADD mirror-pull repo-group lockfile /usr/local/bin/
ADD ssh-config /home/hg/.ssh/config

ADD extra/vct/hgtemplates /repo_local/mozilla/hg_templates
ADD extra/vct/hghooks /repo_local/mozilla/hghooks

ADD extra/vct/hgext/pushlog-legacy/*.py /repo_local/mozilla/extensions/
ADD extra/vct/hgext/pushlog-legacy/parsedatetime/* /repo_local/mozilla/extensions/parsedatetime/
ADD extra/vct/hgext/pushlog/* /repo_local/mozilla/extensions/pushlog/
ADD extra/vct/hgext/serverlog/* /repo_local/mozilla/extensions/serverlog/
RUN ln -sf /repo_local/mozilla/hghooks/mozhghooks /repo_local/mozilla/libraries

ADD hgweb.wsgi hgweb.config /repo_local/mozilla/webroot_wsgi/
ADD set-mirror-key.py /set-mirror-key.py
ADD entrypoint.py /entrypoint.py
ADD run.sh /run.sh

EXPOSE 22
EXPOSE 80

ENTRYPOINT ["/entrypoint.py"]
CMD ["/run.sh"]
