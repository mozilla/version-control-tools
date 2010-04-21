#! /usr/bin/python
#  ***** BEGIN LICENSE BLOCK *****
#  Version: MPL 1.1/GPL 2.0/LGPL 2.1
# 
#  The contents of this file are subject to the Mozilla Public License Version
#  1.1 (the "License"); you may not use this file except in compliance with
#  the License. You may obtain a copy of the License at
#  http://www.mozilla.org/MPL/
# 
#  Software distributed under the License is distributed on an "AS IS" basis,
#  WITHOUT WARRANTY OF ANY KIND, either express or implied. See the License
#  for the specific language governing rights and limitations under the
#  License.
# 
#  The Original Code is [Open Source Virtual Machine.].
# 
#  The Initial Developer of the Original Code is
#  Adobe System Incorporated.
#  Portions created by the Initial Developer are Copyright (C) 2010
#  the Initial Developer. All Rights Reserved.
# 
#  Contributor(s):
#    Adobe AS3 Team
# 
#  Alternatively, the contents of this file may be used under the terms of
#  either the GNU General Public License Version 2 or later (the "GPL"), or
#  the GNU Lesser General Public License Version 2.1 or later (the "LGPL"),
#  in which case the provisions of the GPL or the LGPL are applicable instead
#  of those above. If you wish to allow use of your version of this file only
#  under the terms of either the GPL or the LGPL, and not to allow others to
#  use your version of this file under the terms of the MPL, indicate your
#  decision by deleting the provisions above and replace them with the notice
#  and other provisions required by the GPL or the LGPL. If you do not delete
#  the provisions above, a recipient may use your version of this file under
#  the terms of any one of the MPL, the GPL or the LGPL.
# 
#  ***** END LICENSE BLOCK ****
#
#  Hook script used by tamarin team on tamarin-redux and tamarin-central.
#

if __name__ == '__main__':
    import os, sys, commands, re, platform

    HG_NODE=''
    if os.environ.has_key("HG_NODE"):
        HG_NODE = os.environ["HG_NODE"]
    if HG_NODE == '':
        print("ERROR: unknown HG_NODE")
        sys.exit(1)

    # Look for known unwanted changeids
    status, nodes = commands.getstatusoutput("hg log -r %s:tip --template '{node}\n'" % HG_NODE)
    # if hg log fails, exit but do not block the commit
    if status != 0:
        print("hg log failed, hook exiting")
        sys.exit(0)
    for node in nodes.split():
        if node.startswith("126c6ef95f51"):
            sys.exit("blacklisted changeid found")
        if node.startswith("66eb823ce125"):
            sys.exit("blacklisted changeid found")

    # Look for blacklisted bugs
    blacklist = [
        548077,548842,547258,548098,441280,550269,535446,524263,517679,507624,
        520912,525521,537979,542383,555540,558175,555446,552192,556543,545652,
        555052,551051,550269,555059,507624,520912,525521,535446,537979,542383,
        521270,524263,555097,503358,548842,517679,547258,510070,548098,491355,
        555608,441280,548077,482278,551170,519269,477891,481162,481934,553648,
        'Bug 555610: Add regression testcase'
        ]

    bugs = re.compile('(%s)' % '|'.join([str(bug) for bug in blacklist]))
    status, descs = commands.getstatusoutput("hg log -r %s:tip --template '{desc}\n'" % HG_NODE)
    # if hg log fails, exit but do not block the commit
    if status != 0:
        print("hg log failed, hook exiting")
        sys.exit(0)
    for line in descs.split('\n'):
        if bugs.search(line):
            sys.exit("blacklisted bug found")
    
    sys.exit(0)
