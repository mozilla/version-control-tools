# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

# This Lambda function re-publishes GitHub web hooks on Pulse, an
# AMQP server. The function is meant to be triggered by a new message
# on an SNS topic. (See ``lambda_receive.py``.)

import datetime
import json
import os

import kombu


def get_connection():
    return kombu.Connection(
        hostname='pulse.mozilla.org',
        port=5671,
        userid=os.environ['PULSE_USER'],
        password=os.environ['PULSE_PASSWORD'],
        virtual_host='/',
        ssl=True,
        connect_timeout=5,
    )


def handler(event, context):
    if 'Records' not in event:
        raise Exception('event payload does not match expected; are you using SNS?')

    for record in event['Records']:
        m = json.loads(record['Sns']['Message'])
        p = m['body']

        # Don't republish events for private repositories because that
        # data is supposed to be private!
        if p['repository']['private']:
            print('repository is private; ignoring')
            return

        # The routing key (used for filtering/subscriptions) is composed
        # of the full repo name plus the event name.
        routing_key = '%s/%s' % (p['repository']['full_name'], m['event'])

        # TODO use /v1 once someone unhacks the exchange on the server.
        exchange = 'exchange/github-webhooks/v2'

        print('connecting to pulse...')
        c = get_connection()
        c.connect()
        with c:
            ex = kombu.Exchange(exchange, type='topic')
            producer = c.Producer(exchange=ex,
                                  routing_key=routing_key,
                                  serializer='json')

            data = {
                'event': m['event'],
                'request_id': m['request_id'],
                'payload': p,
                '_meta': {
                    'exchange': exchange,
                    'routing_key': routing_key,
                    'serializer': 'json',
                    'sent': datetime.datetime.utcnow().isoformat(),
                }
            }

            producer.publish(data)
            print('published!')
