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

serverlog.hgweb
   Whether to record requests for hgweb. Defaults to True.

serverlog.ssh
   Whether to record requests for ssh server. Defaults to True.

Logged Messages
===============

syslog messages conform to a well-defined string format:

    [<session id>:]<request id> <action> [<arg0> [<arg1> [...]]]

The first word is a single or colon-delimited pair of UUIDs. This identifier
is used to associate multiple events together.

HTTP requests will have a single UUID. A new UUID will be generated at the
beginning of the request.

SSH sessions will have multiple UUIDs. The first UUID is a session ID. It will
be created when the connection initiates. Subsequent UUIDs will be generated
for each command processed on the SSH server.

The idea is to write "point" events as soon as they happen and to correlate
these point events into higher-level events later. This approach enables
streaming consumers of the log output to identify in-flight requests. If we
buffered log messages until response completion (such as Apache request logs),
we wouldn't haven't a good handle on what the server is actively doing.

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

BEGIN_SSH_SESSION
-----------------

Written when an SSH session starts.

Arguments:

* repo path
* username creating the session

e.g. ``c9417b51-1e4b-11e4-8adf-b8e85631ff68: BEGIN_SSH_SESSION mozilla-central gps``

Note that there is an empty request id for this event!

END_SSH_SESSION
---------------

Written when an SSH session terminates.

Arguments:

* Float wall time of session
* Float CPU time of session

e.g. ``3f74662b-1e4c-11e4-af00-b8e85631ff68: END_SSH_SESSION 1.716 0.000``

BEGIN_SSH_COMMAND
-----------------

Written when an SSH session starts processing a command.

Arguments:

* command name

e.g. ``9bddcd66-1e4e-11e4-af92-b8e85631ff68:9bdf08ab-1e4e-11e4-836d-b8e85631ff68 BEGIN_SSH_COMMAND between``

END_SSH_COMMAND
---------------

Written when an SSH session finishes processing a command.

Arguments:

* Float wall time to process command
* Float CPU time to process command

e.g. ``9bddcd66-1e4e-11e4-af92-b8e85631ff68:9bdf08ab-1e4e-11e4-836d-b8e85631ff68 END_SSH_COMMAND 0.000 0.000``

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
import mercurial.sshserver as sshserver
import mercurial.wireproto as wireproto

import os
import resource
import syslog
import time
import uuid

origcall = protocol.call
origdispatch = wireproto.dispatch

def protocolcall(repo, req, cmd):
    """Wraps mercurial.hgweb.protocol to record requests."""

    req._syslog('BEGIN_PROTOCOL', cmd)
    return origcall(repo, req, cmd)

class syslogmixin(object):
    """Shared class providing an API to do syslog writing."""
    def _populaterepopath(self):
        repopath = self._serverlog.get('path', None)

        if not repopath:
            reporoot = self.repo.ui.config('serverlog', 'reporoot', '')
            if reporoot and not reporoot.endswith('/'):
                reporoot += '/'

            repopath = self.repo.path
            if reporoot and repopath.startswith(reporoot):
                repopath = repopath[len(reporoot):]
            repopath = repopath.rstrip('/').rstrip('/.hg')

        self._serverlog['path'] = repopath

    def _syslog(self, action, *args):
        if not self._serverlog['syslogconfigured']:
            ident = self.repo.ui.config('syslog', 'ident', 'hgweb')
            facility = self.repo.ui.config('syslog', 'facility', 'LOG_LOCAL2')
            facility = getattr(syslog, facility)

            syslog.openlog(ident, 0, facility)
            self._serverlog['syslogconfigured'] = True

        fmt = '%s %s %s'
        formatters = (self._serverlog['requestid'], action, ' '.join(args))
        if self._serverlog.get('sessionid'):
            fmt = '%s:' + fmt
            formatters = tuple([self._serverlog['sessionid']] + list(formatters))

        syslog.syslog(syslog.LOG_NOTICE, fmt % formatters)

class hgwebwrapped(hgweb_mod.hgweb, syslogmixin):
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
        self._serverlog['path'] = req.env.get('REPO_NAME')
        self._populaterepopath()

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

class sshserverwrapped(sshserver.sshserver, syslogmixin):
    """Wrap sshserver class to record events."""

    def serve_forever(self):
        self._serverlog = {
            'sessionid': str(uuid.uuid1()),
            'requestid': '',
            'syslogconfigured': False,
        }

        self._populaterepopath()

        self._syslog('BEGIN_SSH_SESSION',
            self._serverlog['path'],
            os.environ['USER'])

        startusage = resource.getrusage(resource.RUSAGE_SELF)
        startcpu = startusage.ru_utime + startusage.ru_stime
        starttime = time.time()

        try:
            return super(sshserverwrapped, self).serve_forever()
        finally:
            endtime = time.time()
            endusage = resource.getrusage(resource.RUSAGE_SELF)
            endcpu = endusage.ru_utime + endusage.ru_stime

            deltatime = endtime - starttime
            deltacpu = endcpu - startcpu

            self._syslog('END_SSH_SESSION',
                '%.3f' % deltatime,
                '%.3f' % deltacpu)

            syslog.closelog()
            self._serverlog['syslogconfigured'] = False

    def serve_one(self):
        self._serverlog['requestid'] = str(uuid.uuid1())

        def dispatch(repo, proto, cmd):
            self._syslog('BEGIN_SSH_COMMAND', cmd)
            return origdispatch(repo, proto, cmd)

        startusage = resource.getrusage(resource.RUSAGE_SELF)
        startcpu = startusage.ru_utime + startusage.ru_stime
        starttime = time.time()

        wireproto.dispatch = dispatch
        try:
            return super(sshserverwrapped, self).serve_one()
        finally:
            endtime = time.time()
            endusage = resource.getrusage(resource.RUSAGE_SELF)
            endcpu = endusage.ru_utime + endusage.ru_stime

            deltatime = endtime - starttime
            deltacpu = endcpu - startcpu

            self._syslog('END_SSH_COMMAND',
                '%.3f' % deltatime,
                '%.3f' % deltacpu)

            wireproto.dispatch = origdispatch
            self._serverlog['requestid'] = ''

def extsetup(ui):
    protocol.call = protocolcall

    if ui.configbool('serverlog', 'hgweb', True):
        hgweb_mod.hgweb = hgwebwrapped

    if ui.configbool('serverlog', 'ssh', True):
        sshserver.sshserver = sshserverwrapped
