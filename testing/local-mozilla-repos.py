# This software may be used and distributed according to the terms of the
# GNU General Public License version 2 or any later version.

"""Dummy extension to change the URLs of Mozilla repositories to local URLs.

A number of extensions change behavior when interacting with Mozilla
repositories. Answering "is a Mozilla repository" typically works by
examining the repository URL.

Enabling this extension causes local repositories in the test environment
to answer true to "is a Mozilla repository."
"""

import responses

from mozautomation import repository

def extsetup(ui):
    read_uri = ui.config('localmozrepo', 'readuri')
    write_uri = ui.config('localmozrepo', 'writeuri')

    if read_uri:
        repository.BASE_READ_URI = read_uri
    if write_uri:
        repository.BASE_WRITE_URI = write_uri

    responses.start()

    extra = ui.config('localmozrepo', 'execfile', None)
    if extra:
        bzurl = ui.config('bugzilla', 'url')
        execfile(extra)
