#!/usr/bin/python -u
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import json
import os
import sys


execfile('/venv/bin/activate_this.py', dict(__file__='/venv/bin/activate_this.py'))
sys.path.insert(0, '/reviewboard/conf')
os.environ['DJANGO_SETTINGS_MODULE'] = 'reviewboard.settings'

bugzilla_url = 'http://bmoweb'
autoland_url = 'http://autoland'
ldap_url = 'ldap://ldap:389'

# siteconfig takes priority over settings_local.py. Ensure siteconfig
# is up to date.
#
# This code mimics what is done in
# reviewboard.admin.management.sites.migrate_settings(). Its existence is
# unfortunate. If we could guarantee that settings_local.py never changes,
# we wouldn't need this.

from djblets.siteconfig.models import SiteConfiguration
from django.conf import settings
sc = SiteConfiguration.objects.get_current()
caches = getattr(settings, 'CACHES', {})
sc.set('cache_backend', caches)

# Set default logging location
sc.set('logging_enabled', True)
sc.set('logging_directory', '/reviewboard/logs')

# Define Bugzilla URL. We use the internal IP here to do initial setup.
# However, for Bugzilla's authentication-delegation system, we later need to
# reset this to Bugzilla's public IP, which is not available at this point.
# It is later set via set-site-url by vcttesting.mozreview.MozReview.
sc.set('auth_bz_xmlrpc_url', '%s/xmlrpc.cgi' % bugzilla_url)
sc.save()

# Define MozReview settings.
settings = {}
settings['enabled'] = True
settings['pulse_host'] = 'pulse'
settings['pulse_port'] = 5672
settings['pulse_user'] = 'guest'
settings['pulse_password'] = 'guest'
settings['pulse_ssl'] = False
settings['autoland_try_ui_enabled'] = True
settings['autoland_url'] = autoland_url
settings['autoland_user'] = 'autoland'
settings['autoland_password'] = 'autoland'
settings['autoland_testing'] = True
settings['autoland_import_pullrequest_ui_enabled'] = True
settings['ldap_url'] = ldap_url
settings['ldap_user'] = 'uid=bind-mozreview,ou=logins,dc=mozilla'
settings['ldap_password'] = 'password'
settings_path = os.path.join('/', 'mozreview-settings.json')
with open (settings_path, 'w') as f:
    json.dump(settings, f, sort_keys=True)

os.execl(sys.argv[1], *sys.argv[1:])
