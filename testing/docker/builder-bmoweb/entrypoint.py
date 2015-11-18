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

import mysql.connector

# Dirty hack to make stdout unbuffered. This matters for Docker log viewing.
class Unbuffered(object):
   def __init__(self, s):
       self.s = s
   def write(self, d):
       self.s.write(d)
       self.s.flush()
   def __getattr__(self, a):
       return getattr(self.s, a)
sys.stdout = Unbuffered(sys.stdout)

# We also assign stderr to stdout because Docker sometimes doesn't capture
# stderr by default.
sys.stderr = sys.stdout

if 'BMODB_PORT_3306_TCP_ADDR' not in os.environ:
    print('error: container invoked improperly. please link to a bmodb container')
    sys.exit(1)

bz_home = os.environ['BUGZILLA_HOME']
bz_dir = os.path.join(bz_home, 'bugzilla')
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
install_module = False

cc = subprocess.check_call

patches = {
    'apache24.patch',
}
patched_files = {
    '.htaccess',
    'Bugzilla/DB.pm',
    'Bugzilla/Install/Requirements.pm',
    'docker/scripts/generate_bmo_data.pl',
}

existing_patched_files = [p for p in patched_files
                          if os.path.exists(os.path.join(bz_dir, p))]

# Ensure Bugzilla Git clone is up to date.

# First unpatch changed files just in case they get modified.
cc(['/usr/bin/git', 'checkout', '--'] + existing_patched_files, cwd=bz_dir)

# We want container startup to work when offline. So put this behind
# an environment variable that can be specified by automation.
if 'FETCH_BMO' in os.environ:
    cc(['/usr/bin/git', 'fetch', 'origin'], cwd=bz_dir)
    install_module = True

bmo_commit = os.environ.get('BMO_COMMIT', 'origin/master')
cc(['/usr/bin/git', 'checkout', bmo_commit], cwd=bz_dir)

for patch in sorted(patches):
    print('applying patch %s' % patch)
    cc(['/usr/bin/git', 'apply', os.path.join(bz_home, patch)], cwd=bz_dir)

# If we start this and the BMODB container at the same time, MySQL may not be
# running yet. Wait for it.

time_start = time.time()
while True:
    try:
        print('attempting to connect to database...', end='')
        # There appear to be race conditions between MySQL opening the socket
        # and MySQL actually responding. So, we on a successful MySQL
        # connection before continuing.
        mysql.connector.connect(user=db_user, password=db_pass, host=db_host,
                port=db_port)
        print('connected to database at %s:%s as %s' % (db_host, db_port, db_user))
        break
    except (ConnectionError, mysql.connector.errors.Error):
        print('error')

    if time.time() - time_start > db_timeout:
        print('could not connect to database before timeout; giving up')
        sys.exit(1)

    time.sleep(0.100)

j = os.path.join
h = os.environ['BUGZILLA_HOME']
b = j(h, 'bugzilla')
answers = j(h, 'checksetup_answers.txt')

if install_module:
    cc([j(b, 'checksetup.pl'), '--cpanfile'], cwd=b)
    cc(['cpanm', '--installdeps', '--with-recommends', '--with-all-features',
        '--without-feature', 'oracle', '--without-feature', 'sqlite',
        '--without-feature', 'pg', '--without-feature', 'elasticsearch',
        '--notest',
        '.'], cwd=b)

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

if reset_database and not fresh_database:
    print(subprocess.check_output(mysql_args, input=b'DROP DATABASE bugs;'))
    fresh_database = True

# Workaround for bug 1152616.
if fresh_database:
    cc(mysql_args + ['-e', 'CREATE DATABASE %s;' % db_name])

if not os.path.exists(j(h, 'checksetup.done')):
    cc([j(b, 'checksetup.pl',), answers], cwd=b)
    cc([j(b, 'checksetup.pl',), answers], cwd=b)

    # We may not always need -I. When introduced, upstream assumed the modules
    # were already in the default path.
    args = [
        'perl',
        '-I', j(b, 'lib'),
        j(b, 'docker', 'generate_bmo_data.pl'),
        'admin@example.com',
    ]

    subprocess.check_call(args, cwd=b)

    with open(j(h, 'checksetup.done'), 'a'):
        pass

# The base URL is dynamic at container start time. Since we don't always run
# checksetup.pl (because it adds unacceptable container start overhead), we
# hack up the occurrence of this variable in data/params.
params_lines = open(j(b, 'data', 'params'), 'r').readlines()
with open(j(b, 'data', 'params'), 'w') as fh:
    for line in params_lines:
        if "'urlbase' =>" in line:
            fh.write("           'urlbase' => '" + bmo_url + "',\n")
        elif "'mail_delivery_method' =>" in line:
            fh.write("           'mail_delivery_method' => 'Test',\n")
        elif "'auth_delegation' =>" in line:
            fh.write("           'auth_delegation' => 1,\n")
        else:
            fh.write(line)

# Ditto for the database host.
localconfig_lines = open(j(b, 'localconfig'), 'r').readlines()
with open(j(b, 'localconfig'), 'w') as fh:
    def write_variable(k, v):
        fh.write("$%s = '%s';\n" % (k, v))

    for line in localconfig_lines:
        if line.startswith('$db_user'):
            write_variable('db_user', db_user)
        elif line.startswith('$db_pass'):
            write_variable('db_pass', db_pass)
        elif line.startswith('$db_host'):
            write_variable('db_host', db_host)
        elif line.startswith('$db_port'):
            write_variable('db_port', db_port)
        elif line.startswith('$db_name'):
            write_variable('db_name', db_name)
        # The default memory limit is not sufficient to run the BMO
        # configuration. Bump it up.
        elif line.startswith('$apache_size_limit'):
            fh.write('$apache_size_limit = 700_000;\n')
        else:
            fh.write(line)

cc(['/bin/chown', '-R', 'bugzilla:bugzilla', b])

# If the container is aborted, the apache run file will be present and Apache
# will refuse to start.
try:
    os.unlink('/var/run/apache2/apache2.pid')
except FileNotFoundError:
    pass

os.execl(sys.argv[1], *sys.argv[1:])
