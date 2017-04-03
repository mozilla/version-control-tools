# This software may be used and distributed according to the terms of the
# GNU General Public License version 2 or any later version.

"""Conduit client extension.

This extension adds a new command `hg conduitstage` that when targeted at
a remote repo server with the corresponding server extension, will start the
process of staging commits in conduit's commit index, which may later be used
for things such as requesting review.

To use this extension, add a line for it in the extension section of your
.hgrc configuration: conduitext = ~/pathtovct/hgext/conduit-client/client.py
Run tests with `cd vct && python run-tests hgext/conduit-client`
See the README.md for more details.
"""
import os

from mercurial import (
    cmdutil,
    phases,
    util,
)
from mercurial.i18n import _

OUR_DIR = os.path.normpath(os.path.dirname(__file__))
execfile(os.path.join(OUR_DIR, '..', 'bootstrap.py'))

import conduitclient

VERSION = '0.0.1'

testedwith = '4.0 4.1'
minimumhgversion = '4.0'
cmdtable = {}
command = cmdutil.command(cmdtable)
@command('conduitstage',
         [('d', 'drafts', None,
           _('Stage the current commit and its draft ancestors.')),
          ('r', 'rev', '', _('Specify the revision set to stage')),
          ('t', 'topic', '', _('Specify the topic to update'))],
         _('[-d] [-r REV] [-t TOPIC] remote_url'))
def conduitstage(ui, repo, remote_url, drafts=False, rev=None, topic=None):
    """Stages a series of commits as a new Topic Iteration

    Requests the remote repo server to create a new iteration on a topic using
    a list of ids of the commits and the user's bugzilla api credentials.
    Use http://localhost:77777 for the remote_url to test the happy path, this
    is temporary until we setup integration tests with the server extension.
    """
    bz_username = ui.config('bugzilla', 'username', None)
    bz_apikey = ui.config('bugzilla', 'apikey', None)
    if not bz_username or not bz_apikey:
        raise util.Abort(
            _('bugzilla username or apikey not present in .hgrc config'),
            hint=_('make sure that a username and apikey are set in the '
                   'bugzilla section of your .hgrc config'))

    if not rev and not drafts:
        raise util.Abort(
            _('no revision specified and --drafts unset.'),
            hint=_('use either the --rev flag or --drafts flag'))

    revset = rev if rev else '.'
    nodes = get_commits(ui, repo, revset, drafts)
    commit_ids = [repo[node].hex() for node in nodes]

    stage(ui, remote_url, bz_username, bz_apikey, commit_ids, topic)

def get_commits(ui, repo, revset, include_drafts):
    """Creates a list of commit ids given a revision set.

    Creates a list containing the full 40 character ids of the commits in
    the given revset sorted by their order in the commit graph. If only one
    commit is in the revset and include_drafts is true, returns a list of
    all commit ids from the earliest non-public ancestor of the commit
    up to and including the given commit.

    This function is derived from the file below. Thank you to its authors.
    hg.mozilla.org/hgcustom/version-control-tools/hgext/reviewboard/client.py
    """

    # Will abort with a friendly error message if invalid.
    revs = repo.revs(revset)

    # Additional check for valid, empty revision
    if not revs:
        raise util.Abort(
            _('valid revision set turned up empty.'),
            hint=_('e.g. you may have entered 10::6 which turns up empty, '
                   'although 6::10 and 10:6 are both valid.'))

    tipnode = None
    basenode = None
    # Validates that all pushed commits are part of the same DAG head.
    # Note: the revisions are in the order they were specified by the user.
    # This may not be DAG order. So we have to explicitly order them here.
    revs = sorted(repo[r].rev() for r in revs)
    tipnode = repo[revs[-1]].node()
    if len(revs) > 1:
        basenode = repo[revs[0]].node()
    elif len(revs) == 1 and not include_drafts:
        basenode = tipnode

    # Given a base and tip node, find all commits to review.
    # If basenode is specified, we stop the traversal when we encounter it.
    # We do not include public commits.
    nodes = [tipnode]
    # Special case where basenode is the tip node.
    if basenode and tipnode == basenode:
        pass
    else:
        for node in repo[tipnode].ancestors():
            ctx = repo[node]

            if ctx.phase() == phases.public:
                break
            if basenode and ctx.node() == basenode:
                nodes.insert(0, ctx.node())
                break

            nodes.insert(0, ctx.node())

    # Filter out public nodes.
    publicnodes = []
    for node in nodes:
        ctx = repo[node]
        if ctx.phase() == phases.public:
            publicnodes.append(node)
            ui.status(_('(ignoring public commit %s in review request)\n') %
                      ctx.hex()[0:12])

    nodes = [n for n in nodes if n not in publicnodes]
    if not nodes:
        raise util.Abort(
            _('no non-public commits left to review'),
            hint=_('change the given revision set to include draft commits'))

    # We stop completely empty commits prior to review.
    for node in nodes:
        ctx = repo[node]
        if not ctx.files():
            raise util.Abort(
                _('cannot review empty commit %s') % ctx.hex()[:12],
                hint=_('add files to or remove commit'))

    return nodes

def stage(ui, remote_url, bz_username, bz_apikey, commit_ids, topic):
    """Performs the request to stage the commits creating a new iteration."""
    try:
        out = conduitclient.stage(remote_url, bz_username, bz_apikey,
                                  commit_ids, topic)
        ui.status(_(out))
    except Exception as e:
        raise util.Abort(
            _('Failed to publish changes to remote server: %s' % e.message))
