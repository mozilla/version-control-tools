# This software may be used and distributed according to the terms of the
# GNU General Public License version 2 or any later version.

from mercurial import (
    changelog,
    context,
    hg,
    ui,
)

changelog_add = changelog.changelog.add

def add(self, manifest, files, desc, transaction, p1, p2,
        user, date=None, extra=None):
    files = ['foo', 'bar']
    return changelog_add(self, manifest, files, desc, transaction, p1, p2,
        user, date, extra)

changelog.changelog.add = add


if __name__ == '__main__':
    ui = ui.ui()
    repo = hg.repository(ui)
    default_date = '0 0'
    cctx = context.workingctx(repo, 'corrupted', 'foo', default_date,
        {'rebase_source': '0123456789012345678901234567890123456789'})
    repo.commitctx(cctx)
