#!/usr/bin/env python
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

# This script parses serverlog events into unified messages.

import datetime
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

def parse_events(fh):
    requests = {}

    for line in fh:
        date = None
        host = None
        if ' hgweb: ' in line:
            date = line[0:15]
            host = line[16:43]

            if date[4] == ' ':
                date = date[0:4] + '0' + date[5:]
            date = datetime.datetime.strptime(date, '%b %d %H:%M:%S')

            line = line[50:]
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
            repo, ip, url = parts[2:]
            requests[request] = Request(date, repo, ip, url)

        elif action == 'BEGIN_PROTOCOL':
            command = parts[2]
            r = requests.get(request)
            if r:
                r.command = command

        elif action == 'END_REQUEST':
            wr_count, t_wall, t_cpu = parts[2:]
            wr_count = int(wr_count)
            t_wall = float(t_wall)
            t_cpu = float(t_cpu)

            r = requests.get(request)
            if not r:
                continue

            r.write_count = wr_count
            r.wall_time = t_wall
            r.cpu_time = t_cpu
            r.end_date = date
            del requests[request]
            yield r

        elif action == 'BEGIN_SSH_SESSION':
            repo, username = parts[2:]

        elif action == 'END_SSH_SESSION':
            t_wall, t_cpu = parts[2:]
            t_wall = float(t_wall)
            t_cpu = float(t_cpu)

        elif action == 'BEGIN_SSH_COMMAND':
            command = parts[2:]

        elif action == 'END_SSH_COMMAND':
            t_wall, t_cpu = parts[2:]
            t_wall = float(t_wall)
            t_cpu = float(t_cpu)

        elif action == 'CHANGEGROUPSUBSET_START':
            source, count = parts[2:]
            count = int(count)

        elif action == 'WRITE_PROGRESS':
            count = parts[2]
            count = int(count)

def print_stream(fh):
    for r in parse_events(fh):
        if r.start_date:
            d = r.start_date.isoformat()
        else:
            d = 'None'
        print('%s %s %s %s %s %s %s' % (d, r.repo, r.ip, r.command,
            r.write_count, r.wall_time, r.cpu_time))


if __name__ == '__main__':
    if len(sys.argv) > 1:
        for f in sys.argv[1:]:
            with open(f, 'rb') as fh:
                print_stream(fh)
    else:
        print_stream(sys.stdin)
