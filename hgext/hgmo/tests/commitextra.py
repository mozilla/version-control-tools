# This software may be used and distributed according to the terms of the
# GNU General Public License version 2 or any later version.

from mercurial import (
    commands,
    error,
    extensions,
)

def commitcommand(orig, ui, repo, *args, **kwargs):
    extras = {}
    for item in kwargs.pop("extra", []):
        if b'=' not in item:
            raise error.Abort(b"--extra must be in key=value format")
        key, value = item.split(b'=', 1)
        extras[key] = value

    repo._commit_extras = extras
    try:
        return orig(ui, repo, *args, **kwargs)
    finally:
        repo._commit_extras = {}


def tagcommand(orig, ui, repo, *args, **kwargs):
    extras = {}
    for item in kwargs.pop("extra", []):
        if b'=' not in item:
            raise error.Abort(b"--extra must be in key=value format")
        key, value = item.split(b'=', 1)
        extras[key] = value

    repo._commit_extras = extras
    try:
        return orig(ui, repo, *args, **kwargs)
    finally:
        repo._commit_extras = {}


def reposetup(ui, repo):
    if not repo.local():
        return

    class CommitExtraRepo(repo.__class__):
        def commit(self, *args, **kwargs):
            extra = kwargs.get("extra") or {}
            extra.update(getattr(self, "_commit_extras", {}))
            kwargs["extra"] = extra
            return super().commit(*args, **kwargs)

    repo.__class__ = CommitExtraRepo


def extsetup(ui):
    entry = extensions.wrapcommand(commands.table, b"commit", commitcommand)
    entry[1].append(
        (b'', b'extra', [], b'set commit extra metadata (key=value, repeatable)')
    )
    entry = extensions.wrapcommand(commands.table, b"tag", tagcommand)
    entry[1].append(
        (b'', b'extra', [], b'set commit extra metadata (key=value, repeatable)')
    )
