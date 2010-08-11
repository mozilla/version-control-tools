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
# For documentation on hook scripts see:
#   http://hgbook.red-bean.com/read/handling-repository-events-with-hooks.html
#   http://mercurial.selenic.com/wiki/MercurialApi


import sys, re
from mercurial import hg, ui, commands, node


# _quiet function from hghooklib by Johann Duscher
# http://code.google.com/p/hghooklib/
def _quiet(ui, fn):
    oldQuiet = ui.quiet
    ui.quiet = True
    result = fn()
    ui.quiet = oldQuiet
    return result

def master_hook(ui, repo, **kwargs):
    ui.debug('running tamarin master_hook\n')
    ui.debug('kwargs: %s\n' % kwargs)
    # The mercurial hook script expects the equivalent of an exit code back from
    # this call:
    #   False = 0 = No Error : allow push
    #   True = 1 = Error : abort push
    error = False
    error = security_check(ui, repo, **kwargs) or error
    return error

def security_check(ui, repo, **kwargs):
    ui.debug('running security_check\n')
    error = False
    
    ui.pushbuffer()
    _quiet(ui, lambda: commands.log(ui, repo, rev=['%s:tip' % kwargs['node']],
                                    template='{node}\n', date=None, user=None,
                                    logfile=None))
    nodes = ui.popbuffer().split('\n')
    
    # reenable this code if we need to blacklist a node
    '''
    for node in nodes:
        if node.startswith('126c6ef95f51'):
            ui.warn('blacklisted changeid found: node %s is blacklisted\n' % node)
            error = True   # fail the push
    '''
    
    # Look for blacklisted bugs
    blacklist = [
        # crush bugs
        567930,
        # salt bugs
        548842,
        # serrano bugs
        554521,
        ]
    
    bugs = re.compile('(%s)' % '|'.join([str(bug) for bug in blacklist]))
    
    ui.pushbuffer()
    _quiet(ui, lambda: commands.log(ui, repo, rev=['%s:tip' % kwargs['node']],
                                    template='{desc}', date=None, user=None,
                                    logfile=None))
    descs = ui.popbuffer()
    
    searchDescs = bugs.search(descs)
    if searchDescs:
        ui.warn('blacklisted bug found: %s\n' % searchDescs.groups()[0])
        error = True
    
    return error