#!/bin/sh
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

# This script provisions a Vagrant VM for development mode.

set -e

MODULES_DIR='/var/puppet-modules'

if [ ! -f /root/provision.initial ]; then
  apt-get update
  # We don't need chef since we use puppet.
  apt-get -y remove chef
  apt-get -y autoremove
  touch /root/provision.initial
  apt-get -y dist-upgrade
  apt-get -q -y install git ruby-dev
fi

if [ ! -d $MODULES_DIR ]; then
  mkdir -p $MODULES_DIR
fi

cp /version-control-tools/testing/puppet/Puppetfile $MODULES_DIR/Puppetfile

if [ `gem query --local | grep librarian-puppet | wc -l` -eq 0 ]; then
  gem install librarian-puppet
  cd $MODULES_DIR && librarian-puppet install
else
  cd $MODULES_DIR && librarian-puppet update
fi
