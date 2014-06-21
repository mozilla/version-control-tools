# This software may be used and distributed according to the terms of the
# GNU General Public License version 2 or any later version.

"""This file implements a dummy extension that monkeypatches the
post_reviews symbol in the server command handling module so it can
be tested.
"""

import os

from mercurial import extensions

import hgrb.shared

REPO = None

def post_reviews(original, url, username, password, rbid, identifier, commits):
    reviews = []
    if REPO.vfs.exists('DUMMY_REVIEWS'):
        for i, line in enumerate(REPO.vfs('DUMMY_REVIEWS')):
            line = line.strip()
            reviews.append(line)

    lines = []
    parentid = None
    try:
        parentid = str(reviews.index(identifier) + 1)
    except ValueError:
        reviews.append(identifier)
        parentid = str(len(reviews))

    lines.extend([
        'url: %s' % url,
        'username: %s' % username,
        'password: %s' % password,
        'rbid: %s' % rbid,
        'identifier: %s' % identifier,
    ])

    reviewmap = {}
    for i, commit in enumerate(commits['individual']):
        lines.extend([
            str(i),
            commit['id'],
            commit['message'],
            commit['diff'],
            commit['parent_diff'] or 'NO PARENT DIFF'
        ])

        if len(commits['individual']) <= 1:
            reviewmap[commit['id']] = parentid
            continue

        if not commit['rid']:
            reviews.append(commit['id'])

        reviewmap[commit['id']] = commit['rid'] or str(len(reviews))

    lines.append('SQUASHED')
    lines.append(commits['squashed']['diff'])

    REPO.vfs.write('post_reviews', '%s\n' % '\n'.join(lines))
    REPO.vfs.write('DUMMY_REVIEWS', '\n'.join(reviews))

    return parentid, reviewmap

def extsetup(ui):
    extensions.wrapfunction(hgrb.shared, 'post_reviews', post_reviews)

def reposetup(ui, repo):
    global REPO
    REPO = repo
