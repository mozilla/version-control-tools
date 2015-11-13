# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from __future__ import absolute_import, unicode_literals

import time


def wait_for_topic(client, topic, timeout=-1):
    """Wait for a topic to exist on a Kafka connection.

    Sometimes there is a race condition between establishing a Kafka client
    and a topic being created. This function exists to have the client wait for
    a topic to exist before proceeding.
    """
    start = time.time()
    while not client.has_metadata_for_topic(topic):
        if timeout > 0 and time.time() - start > timeout:
            raise Exception('timeout reached waiting for topic')

        time.sleep(0.1)

        # Don't pass topic name to function or it will attempt to create.
        client.load_metadata_for_topics()
