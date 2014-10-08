#!/usr/bin/env python
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

# This script is used to manage Docker containers in the context of running
# Mercurial tests.

import os
import sys

from vcttesting.docker import Docker

def main(args):
    if 'DOCKER_STATE_FILE' in os.environ:
        state_file = os.environ['DOCKER_STATE_FILE']
    elif 'HGTMP' in os.environ:
        state_file = os.path.join(os.environ['HGTMP'], 'docker-state.json')
    else:
        print('Do not know where to put a Docker state file.')
        return 1

    docker_url = os.environ.get('DOCKER_HOST', None)

    d = Docker(state_file, docker_url)

    action = args[0]

    if action == 'build-bmo':
        d.build_bmo(verbose=True)
    elif action == 'start-bmo':
        cluster, http_port = args[1:]
        db_image = os.environ.get('DOCKER_BMO_DB_IMAGE')
        web_image = os.environ.get('DOCKER_BMO_WEB_IMAGE')

        d.start_bmo(cluster=cluster, hostname=None, http_port=http_port,
                db_image=db_image, web_image=web_image)
    elif action == 'stop-bmo':
        d.stop_bmo(cluster=args[1])
    elif action == 'prune-images':
        d.prune_images()

if __name__ == '__main__':
    # Unbuffer stdout.
    sys.stdout = os.fdopen(sys.stdout.fileno(), 'w', 0)

    sys.exit(main(sys.argv[1:]))
