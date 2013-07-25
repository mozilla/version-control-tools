# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from __future__ import unicode_literals

import sqlite3

from .repository import (
    MercurialRepository,
    resolve_trees_to_uris,
)


class ChangeTracker(object):
    """Data store for tracking changes and bugs and repository events."""

    def __init__(self, path):
        self._db = sqlite3.connect(path)

        if not self._schema_current():
            self._create_schema()

    def _schema_current(self):
        return self._db.execute('SELECT COUNT(*) FROM SQLITE_MASTER WHERE '
            'name="trees"').fetchone()[0] == 1

    def _create_schema(self):
        with self._db:
            self._db.execute('CREATE TABLE trees ('
                'id INTEGER PRIMARY KEY AUTOINCREMENT, '
                'name TEXT, '
                'url TEXT '
                ')')

            self._db.execute('CREATE TABLE pushes ('
                'push_id INTEGER, '
                'tree_id INTEGER, '
                'time INTEGER, '
                'user TEXT, '
                'PRIMARY KEY (push_id, tree_id) '
                ')')

            self._db.execute('CREATE TABLE changeset_pushes ('
                'changeset TEXT, '
                'head_changeset TEXT, '
                'push_id INTEGER, '
                'tree_id INTEGER, '
                'UNIQUE (changeset, tree_id) '
                ')')

    def tree_id(self, tree, url=None):
        with self._db:
            field = self._db.execute('SELECT id FROM trees WHERE name=? LIMIT 1',
                [tree]).fetchone()

            if field:
                return field[0]

            self._db.execute('INSERT INTO trees (name, url) VALUES (?, ?)',
                [tree, url])

            return self._db.execute('SELECT id FROM trees WHERE name=? LIMIT 1',
                [tree]).fetchone()[0]

    def load_pushlog(self, tree):
        tree, url = resolve_trees_to_uris([tree])[0]
        repo = MercurialRepository(url)

        tree_id = self.tree_id(tree, url)

        last_push_id = self._db.execute('SELECT push_id FROM pushes WHERE '
            'tree_id=? ORDER BY push_id DESC LIMIT 1', [tree_id]).fetchone()

        last_push_id = last_push_id[0] if last_push_id else -1

        with self._db:
            for push_id, push in repo.push_info(start_id=last_push_id + 1):
                self._db.execute('INSERT INTO pushes (push_id, tree_id, time, '
                'user) VALUES (?, ?, ?, ?)', [push_id, tree_id, push['date'],
                    push['user']])

                head = push['changesets'][0]

                for changeset in push['changesets']:
                    self._db.execute('INSERT INTO changeset_pushes VALUES '
                        '(?, ?, ?, ?)', [changeset, head, push_id, tree_id])

    def pushes_for_changeset(self, changeset):
        for row in self._db.execute('SELECT trees.name, pushes.push_id, '
            'pushes.time, pushes.user, changeset_pushes.head_changeset '
            'FROM trees, pushes, changeset_pushes '
            'WHERE pushes.push_id = changeset_pushes.push_id AND '
            'pushes.tree_id = changeset_pushes.tree_id AND '
            'trees.id = pushes.tree_id AND changeset_pushes.changeset=? '
            'ORDER BY pushes.time ASC', [changeset]):
            yield row
