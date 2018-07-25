#!/usr/bin/env python3
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

# This script can be used to Mozilla-fy Mercurial templates.

import pathlib
import shutil
import subprocess
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

COPY_FILES = {
    'atom/pushlog.tmpl',
    'atom/pushlogentry.tmpl',
    'gitweb_mozilla/firefoxreleases.tmpl',
    'gitweb_mozilla/pushlog.tmpl',
    'gitweb_mozilla/repoinfo.tmpl',
    'static/jquery-1.2.6.min.js',
    'static/livemarks16.png',
    'static/moz-logo-bw-rgb.svg',
}

REPLACEMENTS = [
    # Replace logo HTML.
    (b'<a href="{logourl}" title="Mercurial" style="float: right;">Mercurial</a>',
     b'<div class="logo">\n'
     b'    <a href="{logourl}">\n'
     b'        <img src="{staticurl|urlescape}{logoimg}" alt="mercurial" />\n'
     b'    </a>\n'
     b'</div>'),
]


def main(source_templates, vct_templates_path, new_templates_path):
    # source_templates is the canonical templates to start from.
    # vct_templates is hgtemplates/ from v-c-t.
    # new_templates_path is templates directory to write to. It could be
    # v-c-t's hgtemplates/.

    # vct_templates_path could be the same as new_templates_path and we
    # need to copy files from vct_templates path that may get removed below.
    # So make a copy of all files that may be nuked.
    backups = {}
    for f in COPY_FILES:
        p = vct_templates_path / f
        with p.open('rb') as fh:
            backups[f] = fh.read()

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

    # Create all new files.
    for f in sorted(COPY_FILES):
        dest = new_templates_path / f
        with dest.open('wb') as fh:
            fh.write(backups[f])

    # We need to track all files in the destination so `hg import` below works.
    # TODO we should perhaps be a bit more careful about committing in the case
    # where new_templates_path == vct_templates_path.
    subprocess.run(['hg', 'addremove', '.'],
                   cwd=new_templates_path,
                   check=True)
    subprocess.run(['hg', 'commit', '-m', 'fresh templates'])

    # Apply all our patches.
    patch_dir = vct_templates_path / '.patches'

    for p in sorted(patch_dir.iterdir()):
        if p.suffix != '.patch':
            continue

        subprocess.run(['hg', 'import', str(p.resolve())],
                       cwd=new_templates_path.parent,
                       check=True)
        sys.stderr.flush()
        sys.stdout.flush()

    # Change the logo URL.
    for f in sorted(gitweb_mozilla.iterdir()):
        if f.suffix != '.tmpl':
            continue

        with f.open('rb') as fh:
            s = fh.read()

        for search, replace in REPLACEMENTS:
            if search not in s:
                continue

            print('replacing %s... in %s' % (search[0:24], f))

            s = s.replace(search, replace)

        with f.open('wb') as fh:
            fh.write(s)

    print('committing automated transformations')
    subprocess.run(['hg', 'commit', '-m', 'common rewrites'],
                   cwd=new_templates_path,
                   check=True)


if __name__ == '__main__':
    source_templates, vct_templates, new_templates = sys.argv[1:]

    main(pathlib.Path(source_templates),
         pathlib.Path(vct_templates),
         pathlib.Path(new_templates))
