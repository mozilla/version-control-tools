#!/usr/bin/env python

# Copyright (C) 2011 Mozilla Foundation
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.

import os.path
import re
import argparse

def processMessage(message):
    for line in message.split('\n'):
        match = re.search('try: ',str(line))
        if match:
            line = line.strip().split('try: ', 1)
            line = line[1].split(' ')
            return line
    return [""]

def TryParser(message):
    parser = argparse.ArgumentParser(description='Pass in a commit message and a list \
                                     and tryParse populates the list with the builderNames\
                                     that need schedulers.')
    parser.add_argument('--do-everything', '-a',
                        action='store_true',
                        dest='do_everything',
                        help='m-c override to do all builds, tests, talos just like a trunk push')
    parser.add_argument('--build', '-b',
                        default='do',
                        dest='build',
                        help='accepts the build types requested')
    parser.add_argument('--platform', '-p',
                        default='all',
                        dest='user_platforms',
                        help='provide a list of platforms desired, or specify none (default is all)')
    parser.add_argument('--unittests', '-u',
                        default='all',
                        dest='test',
                        help='provide a list of unit tests, or specify all (default is None)')
    parser.add_argument('--talos', '-t',
                        default='none',
                        dest='talos',
                        help='provide a list of talos tests, or specify all (default is None)')

    (options, unknown_args) = parser.parse_known_args(processMessage(message))

    options.user_platforms = options.user_platforms.split(',')

    return options

def hook(ui, repo, **kwargs):
    name = os.path.basename(repo.root)
    if name != "try":
        return 0;

    options = TryParser(repo.changectx('tip').description())
    if options.do_everything or any(p in options.user_platforms for p in ['all', 'linux', 'linux64']):
        try:
            base = repo.changectx('3a38a70b0e12')
            if repo.changectx('tip').ancestor(base) != base:
                raise
        except:
            print "WARNING: You are pushing a changeset that is likely to fail to build"
            print "on Linux bots if you haven't done something about it."
            print "Please see https://wiki.mozilla.org/ReleaseEngineering/TryServer#Using_older_GCC"
            print "for more details."

    return 0
