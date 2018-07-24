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

serverlog.reporoot
   Root path for all repositories. When logging the repository path, this
   prefix will be stripped.

serverlog.hgweb
   Whether to record requests for hgweb. Defaults to True.

serverlog.ssh
   Whether to record requests for ssh server. Defaults to True.

serverlog.datalogsizeinterval
   Interval (in bytes) between log events when data is being streamed to
   clients. Default value is 10,000,000.

serverlog.blackbox
   Enable blackbox logging using Mercurial's ui.log() facility.

serverlog.blackbox.service
   Service name to use when logging to ui.log(). Defaults to ``hgweb``.

serverlog.syslog
   Enable syslog logging.

serverlog.syslog.ident
   String to prefix all syslog entries with. Defaults to "hgweb".

serverlog.syslog.facility
   String syslog facility to write to. Corresponds to a LOG_* attribute
   in the syslog module. Defaults to LOG_LOCAL2.

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

from __future__ import absolute_import

import gc
import inspect
import os
import resource
import syslog
import time
import uuid
import weakref

from mercurial import (
    error,
    extensions,
    registrar,
    util,
    wireproto,
)
from mercurial.hgweb import (
    hgweb_mod,
    hgwebdir_mod,
)

OUR_DIR = os.path.normpath(os.path.dirname(__file__))
execfile(os.path.join(OUR_DIR, '..', 'bootstrap.py'))

from mozhg.util import import_module

# TRACKING hg46 mercurial.hgweb.protocol effectively renamed to
# mercurial.wireprotoserver
protocol = import_module('mercurial.hgweb.protocol')
wireprotoserver = import_module('mercurial.wireprotoserver')

# TRACKING hg46 mercurial.sshserver renamed to mercurial.wireprotoserver
sshserver = import_module('mercurial.sshserver')

# TRACKING hg46 mercurial.wireprotov1server contains unified code for
# dispatching a wire protocol command
wireprotov1server = import_module('mercurial.wireprotov1server')


testedwith = '4.5'
minimumhgversion = '4.5'

configtable = {}
configitem = registrar.configitem(configtable)

configitem('serverlog', 'blackbox',
           default=True)
configitem('serverlog', 'blackbox.service',
           default='hgweb')
configitem('serverlog', 'reporoot',
           default='')
configitem('serverlog', 'hgweb',
           default=True)
configitem('serverlog', 'ssh',
           default=True)
configitem('serverlog', 'datalogsizeinterval',
           default=10000000)
configitem('serverlog', 'syslog',
           default=True)
configitem('serverlog', 'syslog.ident',
           default='hgweb')
configitem('serverlog', 'syslog.facility',
           'LOG_LOCAL2')

# TRACKING hg46 module removed in 4.6
if protocol:
    origcall = protocol.call


def protocolcall(repo, req, cmd):
    """Wraps mercurial.hgweb.protocol to record requests."""

    # TODO figure out why our custom attribute is getting lost in
    # production.
    if hasattr(repo, '_serverlog'):
        logevent(repo.ui, repo._serverlog, 'BEGIN_PROTOCOL', cmd)

    return origcall(repo, req, cmd)


class fileobjectproxy(object):
    """A proxy around a file object that stores a serverlog reference."""
    __slots__ = (
        '_fp',
        '_serverlog',
    )

    def __init__(self, fp, serverlog):
        object.__setattr__(self, '_fp', fp)
        object.__setattr__(self, '_serverlog', serverlog)

    def __getattribute__(self, name):
        if name in ('_fp', '_serverlog'):
            return object.__getattribute__(self, name)

        return getattr(object.__getattribute__(self, '_fp'), name)

    def __delattr__(self, name):
        return delattr(object.__getattribute__(self, '_fp'), name)

    def __setattr__(self, name, value):
        return setattr(object.__getattribute__(self, '_fp'), name, value)


def wrappeddispatch(orig, repo, proto, command):
    """Wraps wireprotov1server.dispatch() to record command requests."""
    # TRACKING hg46
    # For historical reasons, SSH and HTTP use different log events. With
    # the unification of the dispatch code in 4.6, we could likely unify these.
    # Keep in mind this function is only called on 4.6+: 4.5 has a different
    # code path completely.

    if isinstance(proto, wireprotoserver.httpv1protocolhandler):
        logevent(repo.ui, repo._serverlog, 'BEGIN_PROTOCOL', command)
    elif isinstance(proto, wireprotoserver.sshv1protocolhandler):
        logevent(repo.ui, repo._serverlog, 'BEGIN_SSH_COMMAND', command)

        startusage = resource.getrusage(resource.RUSAGE_SELF)

        repo._serverlog.update({
            'requestid': str(uuid.uuid1()),
            'startcpu': startusage.ru_utime + startusage.ru_stime,
            'starttime': time.time(),
            'ui': weakref.ref(repo.ui),
        })
    else:
        raise error.ProgrammingError('unhandled protocol handler: %r' % proto)

    return orig(repo, proto, command)


def wrappedsshv1respondbytes(orig, fout, rsp):
    # This function is called as part of the main dispatch loop *and* as part
    # of sshv1protocolhandler.getpayload() (which is called by commands that
    # want to read "body" data from the client). We don't want to record a
    # completed command for the latter. There's no good way of only
    # monkeypatching the former. So we sniff the stack for presence of
    # getpayload() and don't do anything special in that case.
    for f in inspect.stack():
        frame = f[0]

        # If there are multiple functions named getpayload() this could give
        # false positives. Until it is a problem, meh.
        if frame.f_code.co_name == r'getpayload':
            return orig(fout, rsp)

    try:
        return orig(fout, rsp)
    finally:
        record_completed_ssh_command(fout)


def wrappedsshv1respondstream(orig, fout, rsp):
    try:
        return orig(fout, rsp)
    finally:
        record_completed_ssh_command(fout)


def wrappedsshv1respondooberror(orig, fout, ferr, message):
    try:
        return orig(fout, ferr, message)
    finally:
        record_completed_ssh_command(fout)


def record_completed_ssh_command(fout):
    serverlog = fout._serverlog
    ui = serverlog['ui']()

    # This should not occur. But weakrefs are weakrefs. Be paranoid.
    if not ui:
        return

    endtime = time.time()
    endusage = resource.getrusage(resource.RUSAGE_SELF)
    endcpu = endusage.ru_utime + endusage.ru_stime

    deltatime = endtime - serverlog['starttime']
    deltacpu = endcpu - serverlog['startcpu']

    logevent(ui, serverlog, 'END_SSH_COMMAND',
             '%.3f' % deltatime,
             '%.3f' % deltacpu)

    del serverlog['ui']
    del serverlog['starttime']
    del serverlog['startcpu']
    serverlog['requestid'] = ''


def repopath(repo):
    root = repo.ui.config('serverlog', 'reporoot')
    if root and not root.endswith('/'):
        root += '/'

    path = repo.path
    if root and path.startswith(root):
        path = path[len(root):]
    path = path.rstrip('/').rstrip('/.hg')

    return path


def logevent(ui, context, action, *args):
    """Log a server event.

    ``context`` is a dict containing state of the session/request.

    ``action`` is the event name and ``args`` are arguments specific to the
    ``action``.
    """
    fmt = '%s %s %s'
    formatters = (context['requestid'], action, ' '.join(args))
    if context.get('sessionid'):
        fmt = '%s:' + fmt
        formatters = tuple([context['sessionid']] + list(formatters))

    if ui.configbool('serverlog', 'blackbox'):
        ui.log(ui.config('serverlog', 'blackbox.service'),
               fmt + '\n', *formatters)

    if ui.configbool('serverlog', 'syslog'):
        logsyslog(ui, fmt % formatters)


def logsyslog(ui, message):
    """Log a formatted message to syslog."""
    ident = ui.config('serverlog', 'syslog.ident')
    facility = getattr(syslog, ui.config('serverlog', 'syslog.facility'))

    syslog.openlog(ident, 0, facility)
    syslog.syslog(syslog.LOG_NOTICE, message)
    syslog.closelog()


class hgwebwrapped(hgweb_mod.hgweb):
    def _runwsgi(self, *args):
        # TRACKING hg46 (req, repo) -> (req, res, repo)
        if len(args) == 3:
            req, res, repo = args
        else:
            req, repo = args

        serverlog = {
            'requestid': str(uuid.uuid1()),
            'writecount': 0,
        }

        # TRACKING hg46 req.env renamed to req.rawenv.
        env = req.rawenv if util.safehasattr(req, 'rawenv') else req.env

        # Resolve the repository path.
        # If serving with multiple repos via hgwebdir_mod, REPO_NAME will be
        # set to the relative path of the repo (I think).
        serverlog['path'] = env.get('REPO_NAME') or repopath(repo)

        serverlog['ip'] = env.get('HTTP_X_CLUSTER_CLIENT_IP') or \
            env.get('REMOTE_ADDR') or 'UNKNOWN'

        # Stuff a reference to the state and the bound logging method so we can
        # record and log inside request handling.
        self._serverlog = serverlog
        repo._serverlog = serverlog

        # TODO REQUEST_URI may not be defined in all WSGI environments,
        # including wsgiref. We /could/ copy code from hgweb_mod here.
        uri = env.get('REQUEST_URI', 'UNKNOWN')

        sl = serverlog
        logevent(repo.ui, sl, 'BEGIN_REQUEST', sl['path'], sl['ip'], uri)

        startusage = resource.getrusage(resource.RUSAGE_SELF)
        startcpu = startusage.ru_utime + startusage.ru_stime
        starttime = time.time()

        datasizeinterval = repo.ui.configint('serverlog', 'datalogsizeinterval')
        lastlogamount = 0

        try:
            for what in super(hgwebwrapped, self)._runwsgi(*args):
                sl['writecount'] += len(what)
                yield what

                if sl['writecount'] - lastlogamount > datasizeinterval:
                    logevent(repo.ui, sl, 'WRITE_PROGRESS',
                             '%d' % sl['writecount'])
                    lastlogamount = sl['writecount']
        finally:
            # It is easy to introduce cycles in localrepository instances.
            # Versions of Mercurial up to and including 4.5 leak repo instances
            # in hgwebdir. We force a GC on every request to help mitigate
            # these leaks.
            gc.collect()

            endtime = time.time()
            endusage = resource.getrusage(resource.RUSAGE_SELF)
            endcpu = endusage.ru_utime + endusage.ru_stime

            deltatime = endtime - starttime
            deltacpu = endcpu - startcpu

            logevent(repo.ui, sl, 'END_REQUEST',
                     '%d' % sl['writecount'],
                     '%.3f' % deltatime,
                     '%.3f' % deltacpu)


# TRACKING hg46 sshserver.sshserver moved to wireprotoserver.sshserver
sshservermod = wireprotoserver if wireprotoserver else sshserver


class sshserverwrapped(sshservermod.sshserver):
    """Wrap sshserver class to record events."""

    def serve_forever(self):
        # TRACKING hg46 self.repo renamed to self._repo.
        if util.safehasattr(self, '_repo'):
            repo = self._repo
        else:
            repo = self.repo

        serverlog = {
            'sessionid': str(uuid.uuid1()),
            'requestid': '',
            'path': repopath(repo),
        }

        # Stuff a reference to the state so we can do logging within repo
        # methods.
        repo._serverlog = serverlog

        # TRACKING hg46 we rely on hacked version of fout file handle in 4.6+.
        if util.safehasattr(self, '_fout'):
            self._fout = fileobjectproxy(self._fout, serverlog)

        logevent(repo.ui, serverlog, 'BEGIN_SSH_SESSION',
                 serverlog['path'],
                 os.environ['USER'])

        self._serverlog = serverlog

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

            logevent(repo.ui, serverlog, 'END_SSH_SESSION',
                     '%.3f' % deltatime,
                     '%.3f' % deltacpu)

            self._serverlog = None

    # TRACKING hg46 this method doesn't exist on 4.6+.
    def serve_one(self):
        self._serverlog['requestid'] = str(uuid.uuid1())

        origdispatch = wireproto.dispatch

        def dispatch(repo, proto, cmd):
            logevent(repo.ui, self._serverlog, 'BEGIN_SSH_COMMAND', cmd)
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

            logevent(self.repo.ui, self._serverlog, 'END_SSH_COMMAND',
                     '%.3f' % deltatime,
                     '%.3f' % deltacpu)

            wireproto.dispatch = origdispatch
            self._serverlog['requestid'] = ''


def extsetup(ui):
    if protocol:
        protocol.call = protocolcall

    if wireprotov1server:
        extensions.wrapfunction(wireprotov1server, 'dispatch',
                                wrappeddispatch)

    if wireprotoserver:
        extensions.wrapfunction(wireprotoserver, '_sshv1respondbytes',
                                wrappedsshv1respondbytes)
        extensions.wrapfunction(wireprotoserver, '_sshv1respondstream',
                                wrappedsshv1respondstream)
        extensions.wrapfunction(wireprotoserver, '_sshv1respondooberror',
                                wrappedsshv1respondooberror)

    if ui.configbool('serverlog', 'hgweb'):
        orighgweb = hgweb_mod.hgweb
        hgweb_mod.hgweb = hgwebwrapped
        hgwebdir_mod.hgweb = hgwebwrapped

        # If running in wsgi mode, this extension may not load until
        # hgweb_mod.hgweb.__init__ is on the stack. At that point, changing
        # module symbols will do nothing: we need to change an actually object
        # instance.
        #
        # So, we walk the stack and see if we have a hgweb_mod.hgweb instance
        # that we need to monkeypatch.
        for f in inspect.stack():
            frame = f[0]
            if 'self' not in frame.f_locals:
                continue

            s = frame.f_locals['self']
            if not isinstance(s, orighgweb):
                continue

            s.__class__ = hgwebwrapped
            break

    if ui.configbool('serverlog', 'ssh'):
        sshservermod.sshserver = sshserverwrapped
