# This software may be used and distributed according to the terms of the
# GNU General Public License version 2 or any later version.

"""Extension that binds a repository to a MozReview user.

Set the mozreview.home and mozreview.username config options and all
operations will use that MozReview user for interacting with services.
"""

import os


def reposetup(ui, repo):
    home = ui.config('mozreview', 'home')
    username = ui.config('mozreview', 'username')
    if not home or not username:
        return

    os.environ['MOZREVIEW_HOME'] = home

    ui.setconfig('bugzilla', 'username', username)

    with open(os.path.join(home, 'credentials', username), 'rb') as fh:
        password = fh.read()
        ui.setconfig('bugzilla', 'password', password)

    os.environ['BUGZILLA_USERNAME'] = username
    os.environ['BUGZILLA_PASSWORD'] = password
