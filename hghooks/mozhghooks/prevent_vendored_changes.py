# This software may be used and distributed according to the terms of the
# GNU General Public License version 2 or any later version.

import grp

from mercurial.node import short


# From hgext/overlay/__init__.py
REVISION_KEY = b"subtree_revision"
SOURCE_KEY = b"subtree_source"


def is_servo_vender_member(user):
    try:
        g = grp.getgrnam("scm_servo_vendor")
        if user in g.gr_mem:
            return True
    except KeyError:
        pass

    return False


def is_servo_allowed(user):
    if is_servo_vender_member(user):
        return True

    return user in {
        b"servo-vcs-sync@mozilla.com",
    }


""""We allow changes to servo created by the prepare-servo-commit hgext.

This gives stylo developers the ability to resolve out of sequence
landing of servo commits.  These commits must meet the following criteria
in order to be considered 'well formed':

- the commit description must match the formatting that servo-vcs-sync
  uses; specifically it must start with "servo: Merge#".
- the commit must only touch files within the /servo directory.
- the commit must contain the extra data that instructs the overlay
  extension (part of servo-vcs-sync) to skip that revision.
"""


def has_fixup_extra_data(ctx):
    # REVISION_KEY must be hex.
    try:
        int(ctx.extra().get(REVISION_KEY), 16)
    except (TypeError, ValueError):
        return False

    # SOURCE_KEY must be URL.
    try:
        return ctx.extra().get(SOURCE_KEY).startswith(b"https://")
    except AttributeError:
        return False


def valid_fixup_description(ctx):
    return ctx.description().startswith(b"servo: Merge #")


def valid_fixup_files(ctx):
    return all(f.startswith(b"servo/") for f in ctx.files())


def is_fixup_commits(repo, nodes):
    """Returns True when all revisions contain valid fixup commit extra data."""
    assert nodes is not None
    for rev in nodes:
        if not has_fixup_extra_data(repo[rev]):
            return False
    return True


def write_error(ui, lines):
    header = b"*" * 72
    ui.write(b"%s\n" % header)
    for line in lines:
        ui.write(b"%s\n" % line)
    ui.write(b"%s\n" % header)


def hook(ui, repo, node, source=None, **kwargs):
    if source in (b"pull", b"strip"):
        return 0

    servonodes = []

    for rev in repo.changelog.revs(repo[node].rev()):
        ctx = repo[rev]
        haveservo = any(f.startswith(b"servo/") for f in ctx.files())

        if haveservo:
            servonodes.append(ctx.node())

    res = 0

    if servonodes:
        ui.write(
            b"(%d changesets contain changes to protected servo/ "
            b"directory: %s)\n" % (len(servonodes), b", ".join(map(short, servonodes)))
        )

        if is_servo_allowed(ui.environ[b"USER"]):
            ui.write(b"(you have permission to change servo/)\n")

        elif is_fixup_commits(repo, servonodes):
            for node in servonodes:
                ctx = repo[node]

                if not valid_fixup_description(ctx):
                    res = 1
                    write_error(
                        ui,
                        [
                            b"invalid servo fixup commit: %s" % short(node),
                            b"",
                            b"commit description is malformed",
                        ],
                    )

                if not valid_fixup_files(ctx):
                    res = 1
                    write_error(
                        ui,
                        [
                            b"invalid servo fixup commit: %s" % short(node),
                            b"",
                            b"commit modifies non-servo files",
                        ],
                    )

                if res == 0:
                    ui.write(
                        b"(allowing valid fixup commit to servo: %s)\n" % short(node)
                    )

        else:
            res = 1
            write_error(
                ui,
                [
                    b"you do not have permissions to modify files under servo/",
                    b"",
                    b"the servo/ directory is kept in sync with the canonical upstream",
                    b"repository at https://github.com/servo/servo",
                    b"",
                    b"changes to servo/ are only allowed by the syncing tool and by sheriffs",
                    b'performing cross-repository "merges"',
                    b"",
                    b"to make changes to servo/, submit a Pull Request against the servo/servo",
                    b"GitHub project",
                ],
            )

    return res
