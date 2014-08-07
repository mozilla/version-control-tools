# This software may be used and distributed according to the terms of the
# GNU General Public License version 2 or any later version.

"""Log requests to a Mercurial server.

The intent of this extension is to log requests to a Mercurial server so
server operators can have better insight into what a server is doing.

The extension is tailored for Mozilla's needs.

Configuration options:

syslog.ident
   String to prefix all syslog entries with. Defaults to "hgweb".

syslog.facility
   String syslog facility to write to. Corresponds to a LOG_* attribute
   in the syslog module.
"""

testedwith = '2.5.4'

import mercurial.hgweb.protocol as protocol

import resource
import syslog
import time
import uuid

origcall = protocol.call

def protocolcall(repo, req, cmd):
    """Wraps mercurial.hgweb.protocol to record requests."""

    ident = repo.ui.config('syslog', 'ident', 'hgweb')
    facility = repo.ui.config('syslog', 'facility', 'LOG_LOCAL5')
    facility = getattr(syslog, facility)

    syslog.openlog(ident, 0, facility)

    reqid = str(uuid.uuid1())
    uri = req.env['REQUEST_URI']
    clientip = req.env.get('HTTP_X_CLUSTER_CLIENT_IP', 'NONE')

    syslog.syslog(syslog.LOG_NOTICE, '%s BEGIN %s %s %s' % (
        reqid, clientip, cmd, uri))

    startusage = resource.getrusage(resource.RUSAGE_SELF)
    startcpu = startusage.ru_utime + startusage.ru_stime
    starttime = time.time()

    writecount = [0]

    def logend():
        endtime = time.time()
        endusage = resource.getrusage(resource.RUSAGE_SELF)
        endcpu = endusage.ru_utime + endusage.ru_stime

        deltatime = endtime - starttime
        deltacpu = endcpu - startcpu
        if deltatime > 0.0:
            cpupercent = deltacpu / deltatime
        else:
            cpupercent = 0.0

        syslog.syslog(syslog.LOG_NOTICE, '%s END %d %.3f %.3f' % (
            reqid, writecount[0], deltatime, cpupercent))
        syslog.closelog()

    # Wrap the iterator returned by the protocol layer to log after iterator
    # exhaustion. This may not log in the case of aborts. Meh.
    class wrappediter(object):
        def __init__(self, it):
            if isinstance(it, list):
                self._it = iter(it)
            else:
                self._it = it

        def __iter__(self):
            return self

        def next(self):
            try:
                what = self._it.next()
                writecount[0] += len(what)
                return what
            except StopIteration:
                logend()
                raise

    return wrappediter(origcall(repo, req, cmd))

def extsetup(ui):
    protocol.call = protocolcall
