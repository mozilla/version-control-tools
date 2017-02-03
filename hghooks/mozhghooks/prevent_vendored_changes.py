# This software may be used and distributed according to the terms of the
# GNU General Public License version 2 or any later version.

import grp
import os

from mercurial.node import short


def isautolandmember(user):
    try:
        g = grp.getgrnam('scm_autoland')
        if user in g.gr_mem:
            return True
    except KeyError:
        pass

    return False


def isservoallowed(user):
    if isautolandmember(user):
        return True

    return user in {
        'gszorc@mozilla.com',
    }


def hook(ui, repo, node, source=None, **kwargs):
    if source in ('pull', 'strip'):
        return 0

    servonodes = []

    for rev in repo.changelog.revs(repo[node].rev()):
        ctx = repo[rev]
        haveservo = any(f.startswith('servo/') for f in ctx.files())

        if haveservo:
            servonodes.append(short(ctx.node()))

    res = 0

    if servonodes:
        ui.write('(%d changesets contain changes to protected servo/ '
                 'directory: %s)\n' % (
                 len(servonodes), ', '.join(servonodes)))

        if isservoallowed(os.environ['USER']):
            ui.write('(you have permission to change servo/)\n')
        else:
            res = 1
            header = '*' * 72
            ui.write('%s\n' % header)
            ui.write('you do not have permissions to modify files under '
                     'servo/\n')
            ui.write('\n')
            ui.write('the servo/ directory is kept in sync with the canonical '
                     'upstream\nrepository at '
                     'https://github.com/servo/servo\n')
            ui.write('\n')
            ui.write('changes to servo/ are only allowed by the syncing tool '
                     'and by sheriffs\nperforming cross-repository "merges"\n')
            ui.write('\n')
            ui.write('to make changes to servo/, submit a Pull Request against '
                     'the servo/servo\nGitHub project\n')
            ui.write('%s\n' % header)

    return res
