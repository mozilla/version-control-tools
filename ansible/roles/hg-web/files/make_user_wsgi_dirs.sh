#!/bin/bash

cd /repo/hg/mozilla/users
for i in $(find . -maxdepth 1 -type d -printf '%f\n')
do
    unset USERDIR
    export USERDIR=/repo/hg/webroot_wsgi/users/$i
    test -d $USERDIR || mkdir $USERDIR
    cd $USERDIR
    if [ \! -f $USERDIR/hgweb.config ]
    then
        echo    "[web]"                                     > hgweb.config
        echo -e "baseurl = http://hg.mozilla.org/users/$i" >> hgweb.config
        echo    "[paths]"                                  >> hgweb.config
        echo -e "/ = /repo/hg/mozilla/users/$i/*"          >> hgweb.config
    fi

    if [ \! -f $USERDIR/hgweb.wsgi ]
    then
        echo    "#!/usr/bin/env python"                                      > hgweb.wsgi
        echo -e "config = '/repo/hg/webroot_wsgi/users/$i/hgweb.config'"    >> hgweb.wsgi
        echo    "from mercurial import demandimport; demandimport.enable()" >> hgweb.wsgi
        echo    "from mercurial.hgweb import hgweb"                         >> hgweb.wsgi
        echo    "import os"                                                 >> hgweb.wsgi
        echo    "os.environ['HGENCODING'] = 'UTF-8'"                        >> hgweb.wsgi
        echo    "application = hgweb(config)"                               >> hgweb.wsgi
    fi
done
