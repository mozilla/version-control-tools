# This software may be used and distributed according to the terms of the
# GNU General Public License version 2 or any later version.

"""Review Board client extension.

This extensions enables clients to easily create Review Board reviews
when pushing to a remote server.

When a client with this extension installed pushes to a remote that has the
corresponding server extension installed, the client will create a Review
Board review automatically.

This extension adds new options to the `push` command:

  * --noreview If present, we will not attempt to perform a review
    automatically when pushing. This is typically only useful for
    testing or ensuring certain commits are present on the remote.
  * --reviewid The review identifier to use. Pushes using the same
    review ID will overwrite existing reviews for that ID.
"""

import os
import sys
import urllib

from mercurial import commands
from mercurial import exchange
from mercurial import extensions
from mercurial import hg
from mercurial import util
from mercurial import wireproto
from mercurial.i18n import _

OUR_DIR = os.path.dirname(__file__)
REPO_ROOT = os.path.normpath(os.path.join(OUR_DIR, '..', '..'))
PYLIB = os.path.join(REPO_ROOT, 'pylib')
sys.path.insert(0, os.path.join(PYLIB, 'mozautomation'))

from mozautomation.commitparser import parse_bugs


def pushcommand(orig, ui, repo, *args, **kwargs):
    repo.noreviewboardpush = kwargs['noreview']
    repo.reviewid = kwargs['reviewid']

    return orig(ui, repo, *args, **kwargs)


def wrappedpush(orig, repo, remote, force=False, revs=None, newbranch=False):
    if not remote.capable('reviewboard'):
        return orig(repo, remote, force=force, revs=revs, newbranch=newbranch)

    if revs and len(revs) > 1:
        raise util.Abort(_('Cannot push to a Review Board repo with multiple '
            '-r arguments. Specify a single revision - the tip revision - '
            'that you would like reviewed.'))

    return orig(repo, remote, force=force, revs=revs, newbranch=newbranch)


def wrappedpushbookmark(orig, pushop):
    result = orig(pushop)

    if not pushop.remote.capable('reviewboard'):
        return result

    ui = pushop.ui
    repo = pushop.repo

    if repo.noreviewboardpush:
        return result

    ui.write(_('Attempting to create a code review...\n'))

    reviewnode = None
    if pushop.revs:
        assert len(pushop.revs) == 1
        reviewnode = repo[pushop.revs[0]].node()
    elif pushop.outgoing.missing:
        reviewnode = pushop.outgoing.missing[-1]
    else:
        ui.write(_('Unable to determine what to review. Please invoke '
            'with -r to specify what to review.\n'))
        return result

    assert reviewnode

    doreview(repo, ui, pushop.remote, reviewnode)

    return result


def doreview(repo, ui, remote, reviewnode):
    """Do the work of submitting a review to a remote repo.

    :remote is a peerrepository.
    :reviewnode is the node of the tip to review.
    """
    assert remote.capable('reviewboard')

    username, password = repo.reviewboardauth()
    if not username or not password:
        ui.write(_('Review Board extension not properly configured: '
            'missing authentication credentials. Please define '
            '"username" and "password" in the [reviewboard] section of '
            'your hgrc.\n'))
        return

    # Given a tip node, we need to find all changesets to review.
    # A solution that works most of the time is to find all non-public
    # ancestors of that node.
    nodes = [repo[reviewnode].hex()]
    for rev in repo[reviewnode].ancestors():
        ctx = repo[rev]
        if ctx.phasestr() == 'public':
            break
        nodes.insert(0, ctx.hex())

    # TODO need ability to manually override review nodes.

    identifier = None

    # Our default identifier comes from the first referenced bug number
    # of the earliest commit.
    # TODO consider making the default the active bookmark.
    for node in nodes:
        ctx = repo[node]
        bugs = parse_bugs(ctx.description())
        if bugs:
            identifier = str(bugs[0])
            break

    if repo.reviewid:
        identifier = repo.reviewid

    if not identifier:
        ui.write(_('Unable to determine review identifier. Review '
            'identifiers are extracted from commit messages automatically. '
            'Try to begin one of your commit messages with "Bug XXXXXX -"\n'))
        return

    ui.write(_('Identified %d changesets for review\n') % len(nodes))
    ui.write(_('Review identifier: %s\n') % identifier)

    lines = [
        urllib.quote(username),
        urllib.quote(password),
        ' '.join(nodes),
        urllib.quote(identifier),
    ]

    ret = remote._call('reviewboard', data='\n'.join(lines))
    ui.write(ret)


def extsetup(ui):
    extensions.wrapfunction(exchange, 'push', wrappedpush)
    # _pushbookmark gets called near the end of push. Sadly, there isn't
    # a better place to hook that has access to the pushop.
    extensions.wrapfunction(exchange, '_pushbookmark', wrappedpushbookmark)

    # Define some extra arguments on the push command.
    entry = extensions.wrapcommand(commands.table, 'push', pushcommand)
    entry[1].append(('', 'noreview', False,
                     _('Do not perform a review on push.')))
    entry[1].append(('', 'reviewid', None, _('Review identifier')))


def reposetup(ui, repo):
    if not repo.local():
        return

    class reviewboardrepo(repo.__class__):
        def __init__(self, *args, **kwargs):
            super(reviewboardrepo, self).__init__(*args, **kwargs)

            self.noreviewboardpush = False
            self.reviewid = None

        def reviewboardauth(self):
            """Obtain the credentials to authenticate with ReviewBoard."""

            # TODO attempt to grab these from Firefox profile automatically.
            # See code in bzexport that does that.
            username = ui.config('reviewboard', 'username', None)
            password = ui.config('reviewboard', 'password', None)

            return username, password

    repo.__class__ = reviewboardrepo
