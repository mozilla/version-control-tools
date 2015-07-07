#!/usr/bin/env python
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

# This script parses serverlog events into unified messages.

import datetime
import optparse
import sys

class Request(object):
    def __init__(self, date, repo, ip, url):
        path = url
        if '?' in path:
            path = path[0:path.find('?')]
        path = path.strip('/')

        self.start_date = date
        self.repo = path
        self.ip = ip
        self.url = url
        self.command = None
        self.write_count = None
        self.wall_time = None
        self.cpu_time = None
        self.end_date = None


class SSHSession(object):
    """Represents a full SSH session."""
    def __init__(self, sid, date, repo, username):
        self.id = sid
        self.start_date = date
        self.repo = repo
        self.username = username
        self.commands = []
        self.current_command = None
        self.wall_time = None
        self.cpu_time = None
        self.end_date = None

    @property
    def session_type(self):
        """Determine the type of the session.

        The following types exist:

          push - New changesets were pushed
          pushkey - New keys were set but no changesets were pushed
          pull - Changesets were retrieved
          lookup - Simple repository lookup. Most likely a no-op push or pull.
        """
        commands = set([t[0] for t in self.commands])

        if 'unbundle' in commands:
            return 'push'

        if 'pushkey' in commands:
            return 'pushkey'

        if 'getbundle' in commands:
            return 'pull'

        return 'lookup'


def parse_events(fh, onlydate=None):
    thisyear = datetime.date.today().year

    requests = {}
    sessions = {}

    for line in fh:
        date = None
        host = None
        if ' hgweb: ' in line:
            date = line[0:15]
            if date[4] == ' ':
                date = date[0:4] + '0' + date[5:]
            date = datetime.datetime.strptime(date, '%b %d %H:%M:%S')
            # Year isn't in the logs and Python defaults to 1900.
            date = date.combine(datetime.date(thisyear, date.month, date.day),
                                date.time())

            hostaction, line = line[16:].split(':', 1)
            host, action = hostaction.split()

            line = line.strip()
        parts = line.rstrip().split()

        ids, action = parts[0:2]
        ids = ids.split(':')

        if len(ids) > 1:
            session = ids[0]
            request = ids[1]
        else:
            session = None
            request = ids[0]

        if action == 'BEGIN_REQUEST':
            if onlydate and date.date() != onlydate:
                continue
            repo, ip, url = parts[2:]
            requests[request] = Request(date, repo, ip, url)

        elif action == 'BEGIN_PROTOCOL':
            command = parts[2]
            r = requests.get(request)
            if r:
                r.command = command

        elif action == 'END_REQUEST':
            r = requests.get(request)
            if not r:
                continue

            wr_count, t_wall, t_cpu = parts[2:]
            wr_count = int(wr_count)
            t_wall = float(t_wall)
            t_cpu = float(t_cpu)

            r.write_count = wr_count
            r.wall_time = t_wall
            r.cpu_time = t_cpu
            r.end_date = date
            del requests[request]
            yield r

        elif action == 'BEGIN_SSH_SESSION':
            if onlydate and date.date() != onlydate:
                continue

            repo, username = parts[2:]
            assert session
            sessions[session] = SSHSession(session, date, repo, username)

        elif action == 'END_SSH_SESSION':
            s = sessions.get(session)
            if not s:
                continue

            t_wall, t_cpu = parts[2:]
            t_wall = float(t_wall)
            t_cpu = float(t_cpu)

            s.end_date = date
            s.wall_time = t_wall
            s.cpu_time = t_cpu

            del sessions[session]
            yield s

        elif action == 'BEGIN_SSH_COMMAND':
            command = parts[2]
            s = sessions.get(session)
            if s:
                s.current_command = (request, command, date)

        elif action == 'END_SSH_COMMAND':
            s = sessions.get(session)
            if not s:
                continue

            t_wall, t_cpu = parts[2:]
            t_wall = float(t_wall)
            t_cpu = float(t_cpu)

            current = s.current_command
            if current and current[0] == request:
                s.commands.append((current[1], current[2], date, t_wall, t_cpu))

            # The request IDs don't match or there is no beginning event.
            # This is weird. We just don't record the command.

            s.current_command = None

        elif action == 'CHANGEGROUPSUBSET_START':
            source, count = parts[2:]
            #count = int(count)

        elif action == 'WRITE_PROGRESS':
            count = parts[2]
            #count = int(count)

def print_stream(fh, onlydate=None):
    for thing in parse_events(fh, onlydate=onlydate):
        if isinstance(thing, Request):
            r = thing
            if r.start_date:
                d = r.start_date.isoformat()
            else:
                d = 'None'
            print('%s %s %s %s %s %s %s' % (d, r.repo, r.ip, r.command,
                r.write_count, r.wall_time, r.cpu_time))
        elif isinstance(thing, SSHSession):
            s = thing
            if s.start_date:
                d = s.start_date.isoformat()
            else:
                d = 'None'
            print('%s %s %s %s %s %s %s' % (d, s.id, s.repo, s.session_type,
                s.username, s.wall_time, s.cpu_time))

if __name__ == '__main__':
    parser = optparse.OptionParser()
    parser.add_option('--date',
                      help='Only extract events on the specified date')

    options, args = parser.parse_args()
    date = None
    if options.date:
        dt = datetime.datetime.strptime(options.date, '%Y-%m-%d')
        date = dt.date()

    if args:
        for f in args:
            with open(f, 'rb') as fh:
                print_stream(fh, onlydate=date)
    else:
        print_stream(sys.stdin, onlydate=date)
