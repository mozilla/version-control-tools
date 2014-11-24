#!/bin/bash
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

# This script just echoes push information and author out to a log file

echo -n "$(date) - $LOGNAME - " >> /var/log/hg-push.log
echo ${PWD/\/repo\/hg\/mozilla\/} >> /var/log/hg-push.log
