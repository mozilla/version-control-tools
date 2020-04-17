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
   Whether to record requests for hgweb. Defaults to False.

serverlog.ssh
   Whether to record requests for ssh server. Defaults to False.

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
import os
import resource
import syslog
import time
import uuid
import weakref

from mercurial import (
    error,
    extensions,
    pycompat,
    registrar,
    wireprotoserver,
    wireprototypes,
    wireprotov1server,
)
from mercurial.hgweb import (
    hgweb_mod,
)

OUR_DIR = os.path.normpath(os.path.dirname(__file__))
with open(os.path.join(OUR_DIR, '..', 'bootstrap.py')) as f:
    exec(f.read())

testedwith = b'4.8 4.9 5.0 5.1 5.2 5.3'
minimumhgversion = b'4.8'

configtable = {}
configitem = registrar.configitem(configtable)

configitem(b'serverlog', b'blackbox',
           default=True)
configitem(b'serverlog', b'blackbox.service',
           default=b'hgweb')
configitem(b'serverlog', b'reporoot',
           default='')
configitem(b'serverlog', b'hgweb',
           default=True)
configitem(b'serverlog', b'ssh',
           default=True)
configitem(b'serverlog', b'datalogsizeinterval',
           default=10000000)
configitem(b'serverlog', b'syslog',
           default=True)
configitem(b'serverlog', b'syslog.ident',
           default=b'hgweb')
configitem(b'serverlog', b'syslog.facility',
           b'LOG_LOCAL2')


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
            'requestid': pycompat.bytestr(uuid.uuid1()),
            'startcpu': startusage.ru_utime + startusage.ru_stime,
            'starttime': time.time(),
            'ui': weakref.ref(repo.ui),
        })
    else:
        raise error.ProgrammingError(b'unhandled protocol handler: %r' % proto)

    # If the return type is a `pushres`, `_sshv1respondbytes` will be called twice.
    # We only want to log a completed SSH event on the second call, so flip the
    # `ignorecall` flag here.
    res = orig(repo, proto, command)
    if isinstance(res, wireprototypes.pushres):
        repo._serverlog['ignorecall'] = True

    return res


def wrapped_getpayload(orig, self):
    '''Wraps `sshv1protocolhandler.getpayload` to mark bytes responses as
    non-terminating.
    '''
    self._fout._serverlog['ignorecall'] = True
    return orig(self)


def wrappedsshv1respondbytes(orig, fout, rsp):
    # check if this response is non-terminating (ie if `wrapped_getpayload`
    # set the flag just before this)
    if fout._serverlog.get('ignorecall'):
        fout._serverlog['ignorecall'] = False
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
             b'%.3f' % deltatime,
             b'%.3f' % deltacpu)

    del serverlog['ui']
    del serverlog['starttime']
    del serverlog['startcpu']
    serverlog['requestid'] = b''


def repopath(repo):
    root = repo.ui.config(b'serverlog', b'reporoot')
    if root and not root.endswith(b'/'):
        root += b'/'

    path = repo.path
    if root and path.startswith(root):
        path = path[len(root):]
    path = path.rstrip(b'/').rstrip(b'/.hg')

    return path


def logevent(ui, context, action, *args):
    """Log a server event.

    ``context`` is a dict containing state of the session/request.

    ``action`` is the event name and ``args`` are arguments specific to the
    ``action``.
    """
    fmt = b'%s %s %s'
    formatters = (context['requestid'], pycompat.bytestr(action), b' '.join(args))
    if context.get('sessionid'):
        fmt = b'%s:' + fmt
        formatters = tuple([context['sessionid']] + list(formatters))

    if ui.configbool(b'serverlog', b'blackbox'):
        ui.log(ui.config(b'serverlog', b'blackbox.service'),
               fmt + b'\n', *formatters)

    if ui.configbool(b'serverlog', b'syslog'):
        logsyslog(ui, fmt % formatters)


def logsyslog(ui, message):
    """Log a formatted message to syslog."""
    ident = pycompat.sysstr(ui.config(b'serverlog', b'syslog.ident'))
    facility_config = pycompat.sysstr(ui.config(b'serverlog', b'syslog.facility'))
    facility = getattr(syslog, facility_config)

    syslog.openlog(ident, 0, facility)
    syslog.syslog(syslog.LOG_NOTICE, pycompat.sysstr(message))
    syslog.closelog()


def wrapped_runwsgi(orig, self, req, res, repo):
    '''Wrap hgweb._runwsgi to capture timing and CPU usage information
    '''
    serverlog = {
        'requestid': pycompat.bytestr(uuid.uuid1()),
        'writecount': 0,
    }

    env = req.rawenv

    # Resolve the repository path.
    # If serving with multiple repos via hgwebdir_mod, REPO_NAME will be
    # set to the relative path of the repo (I think).
    serverlog['path'] = req.apppath or repopath(repo)

    serverlog['ip'] = env.get(b'HTTP_X_CLUSTER_CLIENT_IP') or \
        env.get(b'REMOTE_ADDR') or b'UNKNOWN'

    # Stuff a reference to the state and the bound logging method so we can
    # record and log inside request handling.
    self._serverlog = serverlog
    repo._serverlog = serverlog

    # TODO REQUEST_URI may not be defined in all WSGI environments,
    # including wsgiref. We /could/ copy code from hgweb_mod here.
    uri = env.get(b'REQUEST_URI', b'UNKNOWN')

    sl = serverlog
    logevent(repo.ui, sl, 'BEGIN_REQUEST', sl['path'], sl['ip'], uri)

    startusage = resource.getrusage(resource.RUSAGE_SELF)
    startcpu = startusage.ru_utime + startusage.ru_stime
    starttime = time.time()

    datasizeinterval = repo.ui.configint(b'serverlog', b'datalogsizeinterval')
    lastlogamount = 0

    try:
        for what in orig(self, req, res, repo):
            sl['writecount'] += len(what)
            yield what

            if sl['writecount'] - lastlogamount > datasizeinterval:
                logevent(repo.ui, sl, 'WRITE_PROGRESS',
                         b'%d' % sl['writecount'])
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
                 b'%d' % sl['writecount'],
                 b'%.3f' % deltatime,
                 b'%.3f' % deltacpu)


class sshserverwrapped(wireprotoserver.sshserver):
    """Wrap sshserver class to record events."""

    def serve_forever(self):
        repo = self._repo

        serverlog = {
            'sessionid': pycompat.bytestr(uuid.uuid1()),
            'requestid': b'',
            'path': repopath(repo),
        }

        # Stuff a reference to the state so we can do logging within repo
        # methods.
        repo._serverlog = serverlog

        self._fout = fileobjectproxy(self._fout, serverlog)

        logevent(repo.ui, serverlog, 'BEGIN_SSH_SESSION',
                 serverlog['path'],
                 repo.ui.environ[b'USER'])

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
                     b'%.3f' % deltatime,
                     b'%.3f' % deltacpu)

            self._serverlog = None


def extsetup(ui):
    if wireprotov1server:
        extensions.wrapfunction(wireprotov1server, b'dispatch',
                                wrappeddispatch)

    if wireprotoserver:
        extensions.wrapfunction(wireprotoserver.sshv1protocolhandler, b'getpayload',
                                wrapped_getpayload)
        extensions.wrapfunction(wireprotoserver, b'_sshv1respondbytes',
                                wrappedsshv1respondbytes)
        extensions.wrapfunction(wireprotoserver, b'_sshv1respondstream',
                                wrappedsshv1respondstream)
        extensions.wrapfunction(wireprotoserver, b'_sshv1respondooberror',
                                wrappedsshv1respondooberror)

    if ui.configbool(b'serverlog', b'hgweb'):
        extensions.wrapfunction(hgweb_mod.hgweb, '_runwsgi', wrapped_runwsgi)

    if ui.configbool(b'serverlog', b'ssh'):
        wireprotoserver.sshserver = sshserverwrapped
