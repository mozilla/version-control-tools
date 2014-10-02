#!/usr/bin/python3
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

# This script runs on container start and is used to bootstrap the BMO
# database and start an HTTP server.

import os
import shutil
import socket
import subprocess
import sys
import time

if 'BMODB_PORT_3306_TCP_ADDR' not in os.environ:
    print('error: container invoked improperly. please link to a bmodb container')
    sys.exit(1)

db_host = os.environ['BMODB_PORT_3306_TCP_ADDR']
db_port = os.environ['BMODB_PORT_3306_TCP_PORT']
db_user = os.environ.get('DB_USER', 'root')
db_pass = os.environ.get('DB_PASS', 'password')
db_name = os.environ.get('DB_NAME', 'bugs')
db_timeout = int(os.environ.get('DB_TIMEOUT', '60'))
admin_email = os.environ.get('ADMIN_EMAIL', 'admin@example.com')
admin_password = os.environ.get('ADMIN_PASSWORD', 'password')
bmo_url = os.environ.get('BMO_URL', 'http://localhost:80/')
if not bmo_url.endswith('/'):
    bmo_url += '/'

reset_database = 'RESET_DATABASE' in os.environ

# If we start this and the BMODB container at the same time, MySQL may not be
# running yet. Wait for it.

time_start = time.time()
while True:
    try:
        print('attempting to connect to database...', end='')
        sys.stdout.flush()
        socket.create_connection((db_host, db_port), timeout=1)
        print('success')
        time.sleep(1)
        break
    except socket.error:
        print('error')
    sys.stdout.flush()

    if time.time() - time_start > db_timeout:
        print('could not connect to database before timeout; giving up')
        sys.exit(1)

    time.sleep(1)

j = os.path.join
h = os.environ['BUGZILLA_HOME']
b = j(h, 'bugzilla')
answers = j(h, 'checksetup_answers.txt')

# We aren't allowed to embed environment variable references in Perl code in
# checksetup_answers.txt because Perl executes that file in a sandbox. So we
# hack up the file at run time to be sane.

with open(answers, 'rb') as fh:
    lines = fh.readlines()

lines = [l for l in lines if b'#prune' not in l]

def writeanswer(fh, name, value):
    line = "$answer{'%s'} = '%s'; #prune\n" % (name, value)
    fh.write(line.encode('utf-8'))

with open(answers, 'wb') as fh:
    for line in lines:
        fh.write(line)
        fh.write(b'\n')

    writeanswer(fh, 'db_user', db_user)
    writeanswer(fh, 'db_pass', db_pass)
    writeanswer(fh, 'db_host', db_host)
    writeanswer(fh, 'db_port', db_port)
    writeanswer(fh, 'db_name', db_name)
    writeanswer(fh, 'ADMIN_EMAIL', admin_email)
    writeanswer(fh, 'ADMIN_PASSWORD', admin_password)
    writeanswer(fh, 'urlbase', bmo_url)

mysql_args = [
    '/usr/bin/mysql',
    '-u%s' % db_user,
    '-p%s' % db_pass,
    '-h', db_host,
    '-P', db_port,
]

fresh_database = bool(subprocess.call(mysql_args + ['bugs'],
    stdin=subprocess.DEVNULL))

# checksetup.pl appears to not always refresh data/params if the answers
# have been updated. Force it be removing output.
try:
    shutil.rmtree(j(b, 'data'))
except FileNotFoundError:
    pass

if reset_database and not fresh_database:
    print(subprocess.check_output(mysql_args, input=b'DROP DATABASE bugs;'))
    fresh_database = True

# Component watching throws a fit initializing against a fresh database.
# Disable it.
with open(j(b, 'extensions', 'ComponentWatching', 'disabled'), 'a'):
    pass

subprocess.check_call([j(b, 'checksetup.pl',), answers], cwd=b)
subprocess.check_call([j(b, 'checksetup.pl',), answers], cwd=b)

subprocess.check_call(['/bin/chown', '-R', 'bugzilla:bugzilla', b])

sys.stdout.flush()

os.execl(sys.argv[1], *sys.argv[1:])
