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
    if 'DOCKER_STATE_FILE' not in os.environ:
        print('DOCKER_STATE_FILE must be defined')
        return 1

    docker_url = os.environ.get('DOCKER_HOST', None)

    d = Docker(os.environ['DOCKER_STATE_FILE'], docker_url)

    action = args[0]

    if action == 'build-bmo':
        d.build_bmo()
    elif action == 'start-bmo':
        cluster, http_port = args[1:]
        d.start_bmo(cluster=cluster, hostname=None, http_port=http_port)
    elif action == 'stop-bmo':
        d.stop_bmo(cluster=args[1])
    elif action == 'prune-images':
        d.prune_images()

if __name__ == '__main__':
    # Unbuffer stdout.
    sys.stdout = os.fdopen(sys.stdout.fileno(), 'w', 0)

    sys.exit(main(sys.argv[1:]))
