# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

"""
Project unit tests.
"""

import taskcluster
from mock import Mock
from pytest import raises

from mozreviewpulse.trystarter import TryStarter


def test_uses_custom_taskcluster_url():
    with raises(taskcluster.exceptions.TaskclusterConnectionError) as excinfo:
        TryStarter(Mock(), 'my_custom_url')
    assert 'my_custom_url' in excinfo.value.superExc.message


def test_connections_are_checked_on_init():
    with raises(taskcluster.exceptions.TaskclusterConnectionError) as excinfo:
        TryStarter(Mock(), 'my_custom_url', confirm_connections=True)
    assert 'my_custom_url' in excinfo.value.superExc.message


def test_connection_checks_on_init_can_be_skipped():
    # This should not raise an exception
    TryStarter(Mock(), 'my_custom_url', confirm_connections=False)
