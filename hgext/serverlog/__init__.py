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

serverlog.reporoot
   Root path for all repositories. When logging the repository path, this
   prefix will be stripped.
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
    facility = repo.ui.config('syslog', 'facility', 'LOG_LOCAL2')
    facility = getattr(syslog, facility)

    reporoot = repo.ui.config('serverlog', 'reporoot', '')
    if reporoot and not reporoot.endswith('/'):
        reporoot += '/'

    path = repo.path
    if reporoot and path.startswith(reporoot):
        path = path[len(reporoot):]
    path = path.rstrip('/').rstrip('/.hg')

    syslog.openlog(ident, 0, facility)

    reqid = str(uuid.uuid1())
    uri = req.env['REQUEST_URI']
    clientip = req.env.get('HTTP_X_CLUSTER_CLIENT_IP', 'NONE')

    syslog.syslog(syslog.LOG_NOTICE, '%s BEGIN %s %s %s %s' % (
        reqid, path, clientip, cmd, uri))

    startusage = resource.getrusage(resource.RUSAGE_SELF)
    startcpu = startusage.ru_utime + startusage.ru_stime
    starttime = time.time()

    writecount = 0

    try:
        for chunk in origcall(repo, req, cmd):
            writecount += len(chunk)
            yield chunk
    finally:
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
            reqid, writecount, deltatime, cpupercent))
        syslog.closelog()

def extsetup(ui):
    protocol.call = protocolcall
