# This software may be used and distributed according to the terms of the
# GNU General Public License version 2 or any later version.

from __future__ import absolute_import

import os

from mercurial import demandimport

OUR_DIR = os.path.dirname(__file__)
execfile(os.path.join(OUR_DIR, '..', 'bootstrap.py'))

testedwith = '3.8 3.9 4.0'
minimumhgversion = '3.8'

def critique(ui, repo, entire=False, node=None, **kwargs):
    """Perform a critique of a changeset."""
    # We run into weird import issues when running static analysis if the
    # demandimporter is enabled.
    with demandimport.deactivated():
        from flake8.engine import get_style_guide
        from pycodestyle import DiffReport, parse_udiff

        style = get_style_guide(parse_argv=False, ignore='E128')

        ctx = repo[node]

        # Tell the reporter to ignore lines we didn't touch as part of this change.
        if not entire:
            diff = ''.join(ctx.diff())
            style.options.selected_lines = {}
            for k, v in parse_udiff(diff).items():
                if k.startswith('./'):
                    k = k[2:]

                style.options.selected_lines[k] = v

            style.options.report = DiffReport(style.options)

        deleted = repo.status(ctx.p1().node(), ctx.node()).deleted
        files = [f for f in ctx.files() if f.endswith('.py') and f not in deleted]
        for f in files:
            data = ctx.filectx(f).data()
            style.input_file(f, lines=data.splitlines())

    # Never exit with failure because we don't want to prevent the commit
    # from working.


def critichook(ui, repo, node=None, **opts):
    ctx = repo[node]
    # Don't analyze merges.
    if len(ctx.parents()) > 1:
        return 0

    critique(ui, repo, node=node, **opts)
    return 0


def reposetup(ui, repo):
    ui.setconfig('hooks', 'commit.checkstyle', critichook)
