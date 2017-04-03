# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import requests


MAGIC_TEST_REMOTE_URL = 'http://localhost:77777'
REMOTE_STAGE_ENDPOINT = '/stage'

def stage(remote_url, bz_username, bz_apikey, commit_ids, topic=None):
    """Performs the request to stage the commits creating a new iteration.

    Returns a string of output to give to the user, or will raise an
    Exception, which may include those from requests.exceptions.
    """
    stage_url = remote_url.strip('/') + REMOTE_STAGE_ENDPOINT
    output = ''
    # Magic URL until we have a better way to test integration with
    # the server extension or otherwise can startup a mock server.
    # All other URLS go through the full request, response cycle.
    if remote_url == MAGIC_TEST_REMOTE_URL:
        if topic:
            output += ('Publishing to specific topic: %s\n' % topic)

        output += ('Publishing commits for %s:\n' % bz_username)
        for id in commit_ids:
            output += '%s\n' % id
        return output
    else:
        response = requests.post(stage_url,
                                 data={'bugzilla_username': bz_username,
                                       'bugzilla_api_key': bz_apikey,
                                       'commit_ids': commit_ids,
                                       'topic': topic},
                                 timeout=10)
        response.raise_for_status()
        return response.json()['message']
