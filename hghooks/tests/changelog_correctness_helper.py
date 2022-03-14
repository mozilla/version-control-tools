# This software may be used and distributed according to the terms of the
# GNU General Public License version 2 or any later version.

from mercurial import (
    changelog,
    context,
    hg,
    metadata,
    ui,
)

changelog_add = changelog.changelog.add

def add(self, manifest, files, desc, transaction, p1, p2,
        user, date=None, extra=None, p1copies=None, p2copies=None, *args, **kwargs):
    files = metadata.ChangingFiles()

    for filename in [b'foo', b'bar']:
        files.mark_added(filename)

    return changelog_add(self, manifest, files, desc, transaction, p1, p2,
        user, date=date, extra=extra, *args, **kwargs)

changelog.changelog.add = add


if __name__ == '__main__':
    ui = ui.ui()
    repo = hg.repository(ui)
    default_date = b'0 0'
    cctx = context.workingctx(repo, b'corrupted', b'foo', default_date,
        {b'rebase_source': b'0123456789012345678901234567890123456789'})
    repo.commitctx(cctx)
