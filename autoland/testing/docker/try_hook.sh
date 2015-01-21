#!/bin/bash
hg log -r tip|grep "changeset"|grep -o ":\w\+"|sed "s/:\(.*\)/https:\/\/hg.mozilla.org\/try\/rev\/\1/"
