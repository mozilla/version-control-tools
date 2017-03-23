# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from __future__ import unicode_literals

import binascii
import os
import sqlite3

from .repository import (
    MercurialRepository,
    resolve_trees_to_uris,
)


class ChangeTracker(object):
    """Data store for tracking changes and bugs and repository events."""

    def __init__(self, path):
        self.path = path
        self.created = False
        if not os.path.exists(path):
            self.created = True

        self._db = sqlite3.connect(path)

        # We don't care about data loss because all data can be reconstructed
        # relatively easily.
        self._db.execute('PRAGMA SYNCHRONOUS=OFF')
        self._db.execute('PRAGMA JOURNAL_MODE=WAL')

        self._create_schema(self._schema_version)

    @property
    def _schema_version(self):
        return self._db.execute('PRAGMA user_version').fetchone()[0]

    def _create_schema(self, existing):
        if existing < 2 and not self.created:
            raise Exception("Incompatible local database detected. Delete "
                "database file and try again: %s" % self.path)

        with self._db:
            self._db.execute('CREATE TABLE IF NOT EXISTS trees ('
                'id INTEGER PRIMARY KEY AUTOINCREMENT, '
                'name TEXT, '
                'url TEXT '
                ')')

            self._db.execute('CREATE TABLE IF NOT EXISTS pushes ('
                'push_id INTEGER, '
                'tree_id INTEGER, '
                'time INTEGER, '
                'user TEXT, '
                'PRIMARY KEY (push_id, tree_id) '
                ')')

            self._db.execute('CREATE INDEX IF NOT EXISTS i_pushes_push_id '
                'ON pushes (push_id)')

            self._db.execute('CREATE TABLE IF NOT EXISTS changeset_pushes ('
                'changeset BLOB, '
                'head_changeset BLOB, '
                'push_id INTEGER, '
                'tree_id INTEGER, '
                'UNIQUE (changeset, tree_id) '
                ')')

            self._db.execute('CREATE INDEX IF NOT EXISTS i_changeset_pushes_push_id '
                'ON changeset_pushes (tree_id, push_id)')

            self._db.execute('CREATE TABLE IF NOT EXISTS bug_changesets ('
                'bug INTEGER, '
                'changeset BLOB, '
                'UNIQUE (bug, changeset) '
                ')')

            self._db.execute('CREATE INDEX IF NOT EXISTS i_bug_changesets_bug '
                'ON bug_changesets (bug)')

            self._db.execute('PRAGMA user_version=2')

    def wipe_pushlog(self):
        with self._db:
            for table in ['trees', 'pushes', 'changeset_pushes', 'bug_changesets']:
                self._db.execute('DELETE FROM ' + table)

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

    def last_push_id(self, tree):
        """Return the push ID of the last recorded push to a tree.

        Returns an integer or None if no pushes are recorded.
        """
        tree, url = resolve_trees_to_uris([tree])[0]
        tree_id = self.tree_id(tree, url)

        last_push_id = self._db.execute('SELECT push_id FROM pushes WHERE '
            'tree_id=? ORDER BY push_id DESC LIMIT 1', [tree_id]).fetchone()

        return last_push_id[0] if last_push_id else None

    def load_pushlog(self, tree):
        tree, url = resolve_trees_to_uris([tree])[0]
        repo = MercurialRepository(url)

        tree_id = self.tree_id(tree, url)

        last_push_id = self.last_push_id(tree)
        if last_push_id is None:
            last_push_id = -1

        with self._db:
            for push_id, push in repo.push_info(start_id=last_push_id + 1):
                if not push['changesets']:
                    continue
                self._db.execute('INSERT INTO pushes (push_id, tree_id, time, '
                'user) VALUES (?, ?, ?, ?)', [push_id, tree_id, push['date'],
                    push['user']])

                head = buffer(binascii.unhexlify(push['changesets'][-1]))

                params = [(buffer(binascii.unhexlify(c)), head, push_id,
                    tree_id) for c in push['changesets']]
                self._db.executemany('INSERT INTO changeset_pushes VALUES '
                    '(?, ?, ?, ?)', params)

    def add_pushes(self, tree, pushes):
        """Insert an iterable of pushes for a tree.

        ``pushes`` is an iterable of tuples of (pushid, who, when, nodes).
        """
        tree_id = self.tree_id(tree)

        with self._db:
            for push_id, who, when, nodes in pushes:
                for node in nodes:
                    assert len(node) == 20

                self._db.execute(
                        'INSERT INTO pushes (push_id, tree_id, user, time) '
                        'VALUES (?, ?, ?, ?)', [push_id, tree_id, who, when])
                if nodes:
                    head = buffer(nodes[-1])
                    params = [(buffer(c), head, push_id, tree_id) for c in nodes]
                    self._db.executemany(
                            'INSERT INTO changeset_pushes '
                            '(changeset, head_changeset, push_id, tree_id) '
                            'VALUES (?, ?, ?, ?)', params)

    def pushes_for_changeset(self, changeset):
        for row in self._db.execute('SELECT trees.name, pushes.push_id, '
            'pushes.time, pushes.user, changeset_pushes.head_changeset '
            'FROM trees, pushes, changeset_pushes '
            'WHERE pushes.push_id = changeset_pushes.push_id AND '
            'pushes.tree_id = changeset_pushes.tree_id AND '
            'trees.id = pushes.tree_id AND changeset_pushes.changeset=? '
            'ORDER BY pushes.time ASC', [buffer(changeset)]):
            yield row

    def tree_push_head_changesets(self, tree):
        """Obtain all pushes on a given tree.

        Returns pairs (push_id, head_changeset) like
        `(1, 'a\x00y\x06\xa1\xf8\xad\\0;\x08\x15\xacN\x98!\x16\x8d97')`.

        Use binascii.hexlify to convert to a hexadecimal hash.
        """
        tree, url = resolve_trees_to_uris([tree])[0]
        tree_id = self.tree_id(tree, url)
        for push_id, head in self._db.execute(
            'SELECT push_id, head_changeset '
            'FROM changeset_pushes '
            'WHERE tree_id = ? '
            'GROUP BY head_changeset '
            'ORDER BY push_id ASC', [tree_id]):
            yield push_id, str(head)

    def associate_bugs_with_changeset(self, bugs, changeset):
        """Associate a numeric bug number with a changeset.

        This facilitates rapidly looking up changesets associated with
        bugs.
        """
        if len(changeset) != 20:
            raise ValueError('Expected binary changesets, not hex.')

        with self._db:
            self._db.executemany('INSERT OR REPLACE INTO bug_changesets '
                'VALUES (?, ?)', [(bug, buffer(changeset)) for bug in bugs])

    def changesets_with_bug(self, bug):
        for row in self._db.execute('SELECT changeset FROM bug_changesets WHERE '
            'bug = ?', [bug]):
            yield str(row[0])

    def wipe_bugs(self):
        with self._db:
            self._db.execute('DELETE FROM bug_changesets')
