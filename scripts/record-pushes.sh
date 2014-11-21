#!/bin/bash

echo -n "$(date) - $LOGNAME - " >> /var/log/hg-push.log
echo ${PWD/\/repo\/hg\/mozilla\/} >> /var/log/hg-push.log
