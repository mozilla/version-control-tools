# This software may be used and distributed according to the terms of the
# GNU General Public License version 2 or any later version.

from __future__ import absolute_import


def hook(ui, repo, **kwargs):
    # Trigger tags cache generation.
    repo.tags()
    repo.unfiltered().tags()
