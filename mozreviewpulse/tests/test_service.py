# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

"""
Service-level tests.
"""

import json

import pytest
import taskcluster

from mozreviewpulse.trystarter import TryStarter


@pytest.fixture
def pulse_queue(request, pulse_conn):
    queue = pulse_conn.SimpleBuffer('somequeue')
    request.addfinalizer(queue.close)
    return queue


@pytest.fixture
def fake_taskcluster(mountebank):
    # Return HTTP 200 for all requests
    mountebank.create_stub(
        {'responses': [
            {'is': {
                'statusCode': 200,
            }}
        ]}
    )
    return mountebank


def requests_to_path(mb_client, path):
    """Yield mountebank requests that match the given path."""
    for request in mb_client.get_requests():
        if request['path'] == path:
            yield request


def test_listener_receives_messages_from_queue(pulse_queue):
    pulse_listener = TryStarter(pulse_queue, None, confirm_connections=False)
    payload = {'payload': 'hello'}
    pulse_queue.put(payload)
    message = pulse_listener.get()
    assert message.body == json.dumps(payload)


def test_test_starter_can_ping_taskcluster(fake_taskcluster):
    # Arrange
    # Explicitly say we want to confirm service connections
    TryStarter(pulse_queue, fake_taskcluster.get_endpoint(), confirm_connections=True)

    # Act
    requests = fake_taskcluster.get_requests()

    # Assert
    assert len(requests) == 1
    r = requests.pop()
    assert r['path'] == '/ping'
    assert r['method'] == 'GET'


def test_review_request_starts_task_in_taskcluster(pulse_queue, fake_taskcluster):
    # Consume pulse message that review request posted -> start tasks in taskcluster using HTTP api
    # Arrange
    test_starter = TryStarter(pulse_queue, fake_taskcluster.get_endpoint())
    payload = {'payload': 'hello'}
    pulse_queue.put(payload)

    taskId = 1
    tcq = taskcluster.Queue()
    createTask_path = tcq.makeRoute('createTask', replDict={'taskId': taskId})

    # Act
    test_starter.process_messages()

    # Assert
    created_tasks = list(requests_to_path(
        fake_taskcluster, createTask_path))
    assert len(created_tasks) == 1
    task = created_tasks.pop()
    assert task['method'] == 'POST'


def result_from_taskcluster_does_X_and_posts_back_to_reviewboard():
    # Consume from pulse a taskcluster result -> fetch artifact from S3 -> Post result to RB
    pass