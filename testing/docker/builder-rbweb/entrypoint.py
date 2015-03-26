#!/usr/bin/python3
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import os
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

def ensure_settings_local(path, db_host):
    if not os.path.exists(path):
        return

    lines = []
    with open(path, 'rb') as fh:
        for line in fh:
            line = line.rstrip()
            if line.startswith(b'ALLOWED_HOSTS'):
                line = b"ALLOWED_HOSTS = ['*']"
            elif line.startswith(b"        'HOST':"):
                line = "        'HOST': '%s'," % db_host
                line = line.encode('utf-8')

            lines.append(line)

    with open(path, 'wb') as fh:
        fh.write(b'\n'.join(lines))

if 'RBDB_PORT_3306_TCP_ADDR' not in os.environ:
    print('error: container started without link to "bmodb" container')
    sys.exit(1)

cc = subprocess.check_call

rb_home = os.environ['RB_HOME']
site = os.path.join(rb_home, 'site')
conf = os.path.join(site, 'conf')
settings_local = os.path.join(conf, 'settings_local.py')
py_path = os.path.join(rb_home, 'venv', 'bin')

db_host = os.environ['RBDB_PORT_3306_TCP_ADDR']
db_port = os.environ['RBDB_PORT_3306_TCP_PORT']
db_user = os.environ.get('DB_USER', 'root')
db_pass = os.environ.get('DB_PASS', 'password')
db_name = os.environ.get('DB_NAME', 'reviewboard')
db_timeout = int(os.environ.get('DB_TIMEOUT', '60'))

admin_username = os.environ.get('ADMIN_USERNAME', 'admin+1')
admin_email = os.environ.get('ADMIN_EMAIL', 'admin@example.com')

bugzilla_url = None
if 'BZWEB_PORT_80_TCP' in os.environ:
    bugzilla_url = os.environ['BZWEB_PORT_80_TCP'].replace('tcp://', 'http://')

if 'BUGZILLA_URL' in os.environ:
    bugzilla_url = os.environ['BUGZILLA_URL']

conn = None
time_start = time.time()
while True:
    try:
        print('attempting to connect to database...', end='')
        # There appear to be race conditions between MySQL opening the socket
        # and MySQL actually responding. So, we wait on a successful MySQL
        # connection before continuing.
        conn = mysql.connector.connect(user=db_user, password=db_pass,
            host=db_host, port=db_port)
        print('connected to database at %s:%s as %s' % (db_host, db_port, db_user))
        break
    except (ConnectionError, mysql.connector.errors.Error):
        print('error')

    if time.time() - time_start > db_timeout:
        print('could not connect to database before timeout; giving up')
        sys.exit(1)

    time.sleep(1)

cursor = conn.cursor()
cursor.execute('CREATE DATABASE IF NOT EXISTS reviewboard')
cursor.execute("GRANT ALL PRIVILEGES ON reviewboard.* TO 'reviewboard'@'%' IDENTIFIED BY 'reviewboard'")
cursor.execute('FLUSH PRIVILEGES')
cursor.close()

args = [
    site,
    '--noinput',
    '--domain-name=localhost',
    '--site-root=/',
    '--db-type=mysql',
    '--db-name=reviewboard',
    '--db-user=reviewboard',
    '--db-pass=reviewboard',
    '--db-host', db_host,
    '--cache-type=file',
    '--cache-info', os.path.join(site, 'cache'),
    '--web-server-type=apache',
    '--python-loader=wsgi',
]

if os.path.exists(site):
    action = 'upgrade'
else:
    action = 'install'

# Run this first in case of upgrade, otherwise DB info may not be sane.
ensure_settings_local(settings_local, db_host)

cc([os.path.join(py_path, 'rb-site'), action] + args)

rbmanage = [
    os.path.join(py_path, 'python'),
    '-m', 'reviewboard.manage',
]

print('activating mozreview extension')
cc(rbmanage + ['enable-extension', 'mozreview.extension.MozReviewExtension'],
    cwd=conf)
print('activating rbbz extension')
cc(rbmanage + ['enable-extension', 'rbbz.extension.BugzillaExtension'],
    cwd=conf)

# Normalize the default admin user to be compatible with rbbz.
if action == 'install':
    print('adjusting default admin user')
    cursor = conn.cursor()
    cursor.execute('USE reviewboard')
    cursor.execute("UPDATE auth_user SET password='!', is_superuser=1, "
        "is_staff=1, username=%s, email=%s WHERE id=1",
        (admin_username, admin_email))
    cursor.execute('INSERT INTO rbbz_bugzillausermap (user_id, bugzilla_user_id) '
        'VALUES (1, 1)')
    conn.commit()
    cursor.close()

# Normalize settings_local.py again in the case of initial install.
print('normalizing settings_local.py')
ensure_settings_local(settings_local, db_host)

# Use Bugzilla for authentication.
print('use bugzilla for authentication')
cc(rbmanage + ['set-siteconfig', '--key', 'auth_backend', '--value', 'bugzilla'], cwd=conf)

# The URL likely isn't present for initial bootstrap.
if bugzilla_url:
    xmlrpc_url = '%s/xmlrpc.cgi' % bugzilla_url.rstrip('/')
    print('setting Bugzilla XMLRPC URL: %s' % xmlrpc_url)

    # auth_bz_xmlrpc_url can't be set via set-siteconfig, presumably due to
    # rbbz not declaring it properly. Do it from the Python API.
    env = dict(os.environ)
    env['DJANGO_SETTINGS_MODULE'] = 'reviewboard.settings'
    cc([
        os.path.join(py_path, 'python'),
        '-c',
        "from djblets.siteconfig.models import SiteConfiguration as SC; sc = SC.objects.get_current(); sc.set('auth_bz_xmlrpc_url', '%s'); sc.save()" % xmlrpc_url,
        ], env=env, cwd=conf)
else:
    print('no Bugzilla XMLRPC URL defined; Bugzilla interaction may not work!')

conn.close()

print('normalizing permissions')
cc(['chown', '-R', 'reviewboard:reviewboard', rb_home])

# If the container is aborted, the apache run file will be present and Apache
# will refuse to start.
try:
    os.unlink('/var/run/apache2/apache2.pid')
except FileNotFoundError:
    pass

print('entrypoint script finished executing')
os.execl(sys.argv[1], *sys.argv[1:])
