#!/bin/sh

/sbin/service rsyslog start
/usr/sbin/httpd -DFOREGROUND &
/usr/sbin/sshd -D &
wait
