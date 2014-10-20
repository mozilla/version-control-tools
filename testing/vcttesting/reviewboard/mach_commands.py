# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import os
import subprocess
import sys

from mach.decorators import (
    CommandArgument,
    CommandProvider,
    Command,
)

SETTINGS_LOCAL = """
from __future__ import unicode_literals

import os

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': 'reviewboard.db',
        'USER': '',
        'PASSWORD': '',
        'HOST': '',
        'PORT': '',
    },
}

LOCAL_ROOT = os.path.abspath(os.path.dirname(__file__))
PRODUCTION = False

SECRET_KEY = "mbr7-l=uhl)rnu_dgl)um$62ad2ay=xw+$oxzo_ct!$xefe780"
TIME_ZONE = 'UTC'
LANGUAGE_CODE = 'en-us'
SITE_ID = 1
USE_I18N = True
LDAP_TLS = False
LOGGING_ENABLED = True
LOGGING_LEVEL = "DEBUG"
LOGGING_DIRECTORY = "."
LOGGING_ALLOW_PROFILING = True
DEBUG = True
INTERNAL_IPS = "127.0.0.1"

""".strip()

@CommandProvider
class ReviewBoardCommands(object):
    def __init__(self, context):
        self.old_env = os.environ.copy()

    def _setup_env(self, path):
        """Set up the environment for executing Review Board commands."""
        path = os.path.abspath(path)
        sys.path.insert(0, path)

        self.env = os.environ.copy()
        self.env['PYTHONPATH'] = '%s:%s' % (path, self.env.get('PYTHONPATH', ''))
        os.environ['DJANGO_SETTINGS_MODULE'] = 'reviewboard.settings'
        self.manage = [sys.executable, '-m', 'reviewboard.manage']

        if not os.path.exists(path):
            os.mkdir(path)
        os.chdir(path)

        # Some Django operations put things in TMP. This mucks with concurrent
        # execution. So we pin TMP to the instance.
        tmpdir = os.path.join(path, 'tmp')
        if not os.path.exists(tmpdir):
            os.mkdir(tmpdir)
        self.env['TMPDIR'] = tmpdir

        return path


    @Command('create', category='reviewboard',
        description='Create a Review Board server install.')
    @CommandArgument('path', help='Where to create RB install.')
    def create(self, path):
        path = self._setup_env(path)

        with open(os.path.join(path, 'settings_local.py'), 'wb') as fh:
            fh.write(SETTINGS_LOCAL)

        # TODO figure out how to suppress logging when invoking via native
        # Python API.
        f = open(os.devnull, 'w')
        subprocess.check_call(self.manage + ['syncdb', '--noinput'], cwd=path,
                env=self.env, stdout=f, stderr=f)

        subprocess.check_call(self.manage + ['enable-extension',
            'rbbz.extension.BugzillaExtension'], cwd=path,
            env=self.env, stdout=f, stderr=f)

        subprocess.check_call(self.manage + ['enable-extension',
            'rbmozui.extension.RBMozUI'],
            cwd=path, env=self.env, stdout=f, stderr=f)

        from reviewboard.cmdline.rbsite import Site, parse_options
        class dummyoptions(object):
            no_input = True
            site_root = '/'
            db_type = 'sqlite3'
            copy_media = True

        site = Site(path, dummyoptions())
        site.rebuild_site_directory()

        from djblets.siteconfig.models import SiteConfiguration
        sc = SiteConfiguration.objects.get_current()
        sc.set('site_static_root', os.path.join(path, 'htdocs', 'static'))
        sc.set('site_media_root', os.path.join(path, 'htdocs', 'media'))

        # Hook up rbbz authentication.
        sc.set('auth_backend', 'bugzilla')
        sc.set('auth_bz_xmlrpc_url', '%s/xmlrpc.cgi' % os.environ['BUGZILLA_URL'])

        sc.save()

    @Command('repo', category='reviewboard',
        description='Add a repository to Review Board')
    @CommandArgument('path', help='Path to ReviewBoard install.')
    @CommandArgument('name', help='Name to give to this repository.')
    @CommandArgument('url', help='URL this repository should be accessed under.')
    def repo(self, path, name, url):
        path = self._setup_env(path)

        from reviewboard.scmtools.models import Repository, Tool
        tool = Tool.objects.get(name__exact='Mercurial')
        r = Repository(name=name, path=url, tool=tool)
        r.save()
