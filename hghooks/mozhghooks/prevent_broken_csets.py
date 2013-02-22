#!/usr/bin/python
# Copyright (C) 2013 Mozilla Foundation
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
'''This hook detects csets which hit hg bug 3833 [1] and break our hg blame.

An example of one such bad commit is dad25c17ccc7 in mozilla-central.

This hook should be used as a pre-commit hook on all trees except try.

[1] http://bz.selenic.com/show_bug.cgi?id=3833.
'''

from __future__ import print_function
import sys
import traceback
import textwrap
from mercurial import ui, scmutil, cmdutil
from mercurial.node import hex, short, nullid

magicwords = 'IGNORE BROKEN CHANGESETS'

def dedent_and_fill(s):
    r'''This is like textwrap.fill(textwrap.dedent(s)) except it respects
    paragraphs in the text.  That is, " foo\n\n bar" is rendered as
    "foo\n\nbar", instead of "foo bar".

    This function also adds a blank line to the beginning of the input.

    '''
    s = textwrap.dedent(s)

    paragraphs = ['']
    current_paragraph = []
    for line in s.split('\n'):
        if line.strip():
            current_paragraph.append(line)
        elif current_paragraph:
            paragraphs.append(' '.join(current_paragraph))
            paragraphs.append('')
            current_paragraph = []
    if current_paragraph:
        paragraphs.append(' '.join(current_paragraph))

    return '\n'.join([textwrap.fill(p) for p in paragraphs])

class BrokenCsetException(Exception):
    def __init__(self, cset):
        self.cset = cset

    def __str__(self):
        return 'Broken changeset: %s' % str(self.cset)

def hook(ui, repo, hooktype, node, **kwargs):
    if repo.changectx('tip').description().find(magicwords) != -1:
        print(dedent_and_fill('''\
            Not checking this push for broken changesets because the tip cset
            contains %s.  I hope you mean it!
            ''' % magicwords))
        return 0

    try:
        check_for_broken_csets(repo, node)
    except BrokenCsetException as e:
        print(dedent_and_fill('''\
            Broken changeset detected: %s!

            Our pre-commit hook detected a broken changeset in your push: %s.
            This changeset was likely produced by a version of hg older than
            2.5.  We're rejecting your push because this cset may break hg
            blame [1].

            Please upgrade to hg 2.5.1 or newer (2.5 contains known bugs),
            qimport your changes, then qpop, qpush, and qfinish them.  You
            might do:

              $ hg qimport --rev 'outgoing()'
              $ hg qpop -a && hg qpush -a && hg qfinish -a

            If this doesn't solve the problem, or if you're sure that these
            commits were generated using hg 2.5 or newer, please ask someone in
            #it, or file a bug.

            You can work around this hook by putting "%s" in your topmost
            changeset, but please don't use this lightly.

            [1] https://bugzilla.mozilla.org/show_bug.cgi?id=843081
            ''' %
            (e.cset, e.cset, magicwords)))

        # Reject the push.
        return 1
    except Exception:
        print(dedent_and_fill('''\
            WARNING: The prevent_broken_csets pre-commit hook encountered an
            unexpected error.  We're going to allow your push to go through,
            but please ping someone in #it or file a bug in

              mozilla.org :: Server Operations: Developer Services

            so that the right people are informed of this issue.  Thanks!
            '''))
        traceback.print_exc(file=sys.stdout)

    # Accept the push
    return 0

def check_for_broken_csets(repo, push_root):
    '''Check for broken changesets.  If we find one, we raise a
    BrokenCsetException.  Otherwise we return without error.

    '''
    push_root_node = repo[push_root]

    # Gather all the leaf nodes in this push.  There should be at least one; I
    # don't know what it means to push without any leaves!
    leaves = []
    for change_id in xrange(push_root_node.rev(), len(repo)):
        n = repo[change_id]
        if not n.children():
            leaves.append(n)

    if not leaves:
        print(dedent_and_fill('''\
            WARNING: No leaf nodes in this push?  This is probably a bug
            in the commit hook.  Please ask someone in #it about this, or
            file a bug in

              mozilla.org :: Server Operations: Developer Services.

            In the meantime, we won't reject your push.'''))
        return

    # For each leaf, gather the set of files modified between the leaf and the
    # parent(s) of the base commit.
    modified_files = set()
    for leaf_node in leaves:
        for p in push_root_node.parents():
            modified_files.update(repo.status(node1=p, node2=leaf_node)[0])

    # Check each of these files' debugindex entries.
    for filename in modified_files:
        check_debugindex(repo, filename, push_root_node.rev())

def check_debugindex(repo, filename, min_rev):
    '''Check hg's debugindex for filename for bad csets.  A cset is bad if both parents
    are null and if it comes from this push (i.e., linkrev >= min_rev).

    If we find a bad changeset, we throw a BrokenCsetException.

    '''
    # I don't entirely understand what this does, but it's similar to the
    # debugindex command in hg's commands.py.  See also
    # http://bz.selenic.com/show_bug.cgi?id=3833#c20

    r = cmdutil.openrevlog(repo, 'debugindex', filename,
                           {'changelog': False, 'manifest': False})
    for i in r:
        node = r.node(i)
        linkrev = repo[r.linkrev(i)]
        if linkrev.rev() < min_rev:
            continue
        try:
            parents = r.parents(node)
        except Exception:
            parents = (nullid, nullid)

        # If this file has no parents, check whether the relevant rev modified
        # the file (as opposed to, for example, adding it).  If the rev did
        # modify the file, then this is a bad changeset.
        if parents == (nullid, nullid) and \
           filename in repo.status(node1=linkrev.p1(), node2=linkrev)[0]:
                raise BrokenCsetException(linkrev)
