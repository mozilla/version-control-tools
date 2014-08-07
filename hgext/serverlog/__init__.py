# This software may be used and distributed according to the terms of the
# GNU General Public License version 2 or any later version.

"""Log requests to a Mercurial server.

The intent of this extension is to log requests to a Mercurial server so
server operators can have better insight into what a server is doing.

The extension is tailored for Mozilla's needs.

Installing
==========

In your hgrc, add the following:

    [extensions]
    serverlog = /path/to/version-control-tools/hgext/serverlog

Configuration Options
=====================

syslog.ident
   String to prefix all syslog entries with. Defaults to "hgweb".

syslog.facility
   String syslog facility to write to. Corresponds to a LOG_* attribute
   in the syslog module. Defaults to LOG_LOCAL2.

serverlog.reporoot
   Root path for all repositories. When logging the repository path, this
   prefix will be stripped.

Logged Messages
===============

syslog messages conform to a well-defined string format:

    <request id> <action> [<arg0> [<arg1> [...]]]

The actions are defined in the following sections.

BEGIN_REQUEST
-------------

Written when a new request comes in. This occurs for all HTTP requests.

Arguments:

* repo path
* client ip ("UNKNOWN" if not known)
* URL path and query string

e.g. ``bc286e11-1e44-11e4-8889-b8e85631ff68 BEGIN_REQUEST server2 127.0.0.1 /?cmd=capabilities``

BEGIN_PROTOCOL
--------------

Written when a command from the wire protocol is about to be executed. This
almost certainly derives from a Mercurial client talking to the server (as
opposed to say a browser viewing HTML).

Arguments:

* command name

e.g. ``bc286e11-1e44-11e4-8889-b8e85631ff68 BEGIN_PROTOCOL capabilities``

END_REQUEST
-----------

Written when a request finishes and all data has been sent.

There should be an ``END_REQUEST`` for every ``BEGIN_REQUEST``.

Arguments:

* Integer bytes written to client
* Float wall time to process request
* Float CPU time to process request

e.g. ``bc286e11-1e44-11e4-8889-b8e85631ff68 END 0 0.002 0.002``

Limitations
===========

The extension currently only uses syslog for writing events.

The extension assumes only 1 thread is running per process. If multiple threads
are running, CPU time calculations will not be accurate. Other state may get
mixed up.
"""

testedwith = '2.5.4'

import mercurial.hgweb.protocol as protocol
import mercurial.hgweb.hgweb_mod as hgweb_mod

import resource
import syslog
import time
import uuid

origcall = protocol.call

def protocolcall(repo, req, cmd):
    """Wraps mercurial.hgweb.protocol to record requests."""

    req._syslog('BEGIN_PROTOCOL', cmd)
    return origcall(repo, req, cmd)

class hgwebwrapped(hgweb_mod.hgweb):
    def run_wsgi(self, req):
        self._serverlog = {
            'syslogconfigured': False,
            'requestid': str(uuid.uuid1()),
            'uri': req.env['REQUEST_URI'],
            'writecount': 0,
        }

        # Resolve the repository path.
        # If serving with multiple repos via hgwebdir_mod, REPO_NAME will be
        # set to the relative path of the repo (I think).
        repopath = req.env.get('REPO_NAME')
        if not repopath:
            reporoot = self.repo.ui.config('serverlog', 'reporoot', '')
            if reporoot and not reporoot.endswith('/'):
                reporoot += '/'

            repopath = self.repo.path
            if reporoot and repopath.startswith(reporoot):
                repopath = repopath[len(reporoot):]
            repopath = repopath.rstrip('/').rstrip('/.hg')

        self._serverlog['path'] = repopath

        self._serverlog['ip'] = req.env.get('HTTP_X_CLUSTER_CLIENT_IP') or \
            req.env.get('REMOTE_ADDR') or 'UNKNOWN'

        # Stuff a reference to the state and the bound logging method so we can
        # record and log inside request handling.
        req._serverlog = self._serverlog
        req._syslog = self._syslog

        sl = self._serverlog
        self._syslog('BEGIN_REQUEST', sl['path'], sl['ip'], sl['uri'])

        startusage = resource.getrusage(resource.RUSAGE_SELF)
        startcpu = startusage.ru_utime + startusage.ru_stime
        starttime = time.time()

        try:
            for what in super(hgwebwrapped, self).run_wsgi(req):
                self._serverlog['writecount'] += len(what)
                yield what
        finally:
            endtime = time.time()
            endusage = resource.getrusage(resource.RUSAGE_SELF)
            endcpu = endusage.ru_utime + endusage.ru_stime

            deltatime = endtime - starttime
            deltacpu = endcpu - startcpu

            self._syslog('END_REQUEST', '%d' % sl['writecount'], '%.3f' % deltatime,
                '%.3f' % deltacpu)

            syslog.closelog()
            self._serverlog['syslogconfigured'] = False

    def _syslog(self, action, *args):
        if not self._serverlog['syslogconfigured']:
            ident = self.repo.ui.config('syslog', 'ident', 'hgweb')
            facility = self.repo.ui.config('syslog', 'facility', 'LOG_LOCAL2')
            facility = getattr(syslog, facility)

            syslog.openlog(ident, 0, facility)
            self._serverlog['syslogconfigured'] = True

        msg = '%s %s %s' % (self._serverlog['requestid'], action,
            ' '.join(args))
        try:
            syslog.syslog(syslog.LOG_NOTICE, msg)
        except Exception as e:
            pass

def extsetup(ui):
    protocol.call = protocolcall

    hgweb_mod.hgweb = hgwebwrapped
