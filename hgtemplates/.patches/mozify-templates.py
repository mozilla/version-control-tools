#!/usr/bin/env python3
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

# This script can be used to Mozilla-fy Mercurial templates.

import pathlib
import shutil
import sys


REMOVE_DIRS = {
    'coal',
    'monoblue',
    'spartan',
}

REMOVE_FILES = {
    'static/background.png',
    'static/style-extra-coal.css',
    'static/style-monoblue.css',
}


def main(source_templates, vct_templates_path, new_templates_path):
    # source_templates is the canonical templates to start from.
    # vct_templates is hgtemplates/ from v-c-t.
    # new_templates_path is templates directory to write to. It could be
    # v-c-t's hgtemplates/.

    # Ensure new_templates_path is empty.
    if new_templates_path.exists():
        # But take care not to nuke the .patches directory.
        if new_templates_path == vct_templates_path:
            for p in new_templates_path.iterdir():
                if p.name == '.patches':
                    continue

                if p.is_dir():
                    shutil.rmtree(p)
                else:
                    p.unlink()
        else:
            shutil.rmtree(new_templates_path)

    new_templates_path.mkdir(parents=True, exist_ok=True)

    # Make a pristine copy from the canonical templates. In the case
    # where vct_templates_path == new_templates_path we can't simply
    # shutil.copytree() because the destination exists. So we copy everything
    # in the root directory separately.
    for p in source_templates.iterdir():
        if p.is_dir():
            shutil.copytree(p, new_templates_path / p.name)
        else:
            shutil.copyfile(p, new_templates_path / p.name)

    # Remove files and directories that we don't want.
    for d in sorted(REMOVE_DIRS):
        d = new_templates_path / d
        shutil.rmtree(d)

    for f in sorted(REMOVE_FILES):
        f = new_templates_path / f
        f.unlink()

    # Now nuke gitweb_mozilla and make a fresh copy from gitweb.
    gitweb_mozilla = new_templates_path / 'gitweb_mozilla'

    if gitweb_mozilla.exists():
        shutil.rmtree(gitweb_mozilla)

    shutil.copytree(new_templates_path / 'gitweb', gitweb_mozilla)


if __name__ == '__main__':
    source_templates, vct_templates, new_templates = sys.argv[1:]

    main(pathlib.Path(source_templates),
         pathlib.Path(vct_templates),
         pathlib.Path(new_templates))
