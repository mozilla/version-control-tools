#!/usr/bin/env python

# This is derived from treestatus/testapp.py but is modififed to accept
# external connections.
# TODO: we should add host, port and default user arguments upstream so we
#       don't need our own copy.

import os
import treestatus.app
import treestatus.model as model

import sqlite3


def main():
    app = treestatus.app.wsgiapp({
        'here': os.curdir,
        'sqlalchemy.url': 'sqlite:///treestatus.db',
        'debug': True,
    })

    model.DbBase.metadata.create_all()

    # Create a sheriff user
    db = sqlite3.connect('/treestatus.db')
    try:
        db.execute('insert into users values(1, "sheriff@example.com", 1, 1)')
        db.commit()
    except sqlite3.IntegrityError:
        # Hopefully this means our user already exists
        pass
    db.close()

    app.run(host='0.0.0.0', port=80)

if __name__ == '__main__':
    main()
