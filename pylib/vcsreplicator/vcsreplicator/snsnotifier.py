# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from __future__ import absolute_import, print_function, unicode_literals

import datetime
import json
import logging
import os
import sys

import boto3

from .pushnotifications import (
    run_cli,
)


logger = logging.getLogger('vcsreplicator.snsnotifier')


def on_event(config, message_type, partition, message, created, data):
    """Called when a replication message should be handled."""
    repo_url = data['repo_url']

    logger.warn('processing message %d: %s for %s' % (
        message.offset, message_type, repo_url))

    c = config.c

    if c.has_option('awsevents', 's3_endpoint_url'):
        s3_endpoint_url = c.get('awsevents', 's3_endpoint_url')
    else:
        s3_endpoint_url = None

    if c.has_option('awsevents', 'sns_endpoint_url'):
        sns_endpoint_url = c.get('awsevents', 'sns_endpoint_url')
    else:
        sns_endpoint_url = None

    access_key_id = c.get('awsevents', 'access_key_id')
    secret_access_key = c.get('awsevents', 'secret_access_key')
    region = c.get('awsevents', 'region')
    topic_arn = c.get('awsevents', 'topic_arn')
    bucket = c.get('awsevents', 'bucket')

    session = boto3.Session(aws_access_key_id=access_key_id,
                            aws_secret_access_key=secret_access_key,
                            region_name=region)

    s3 = session.client('s3', endpoint_url=s3_endpoint_url)
    sns = session.client('sns', endpoint_url=sns_endpoint_url)

    # We upload the event to S3 for later reference. To prevent multiple
    # copies of the same object and to ensure decent ordering, we put
    # the Kafka partition offset and the original message data in the
    # key name.
    dt = datetime.datetime.utcfromtimestamp(created)
    key = 'events/%s/%010d-%s.json' % (dt.date().isoformat(),
                                       message.offset,
                                       dt.strftime('%Y%m%dT%H%M%S'))

    s3_data = json.dumps({
        'created': created,
        'id': message.offset,
        'type': message_type,
        'data': data,
    }, sort_keys=True)

    s3_url = '%s/%s/%s' % (s3.meta.endpoint_url, bucket, key)

    sns_data = json.dumps({
        'type': message_type,
        'data': data,
        'data_url': s3_url,
    }, sort_keys=True)

    # SNS has a message size limit of 256 KB (262,144 bytes). If our message
    # is too large for SNS, set a key indicating data is external and only
    # available in S3.
    if len(sns_data) > 260000:
        logger.warn('message too large for SNS; dropping payload')
        sns_data = json.dumps({
            'type': message_type,
            'data_url': s3_url,
            'external': True,
            'repo_url': repo_url,
        }, sort_keys=True)

    logger.warn('uploading to S3: %s' % s3_url)
    s3.put_object(Bucket=bucket, Key=key, Body=s3_data,
                  ContentType='application/json')

    logger.warn('sending SNS notification to %s' % topic_arn)
    sns.publish(
        TopicArn=topic_arn,
        Message=sns_data,
    )

    logger.warn('finished processing message %d' % message.offset)

def cli():
    # Unbuffer stdout.
    sys.stdout = os.fdopen(sys.stdout.fileno(), 'w', 1)

    def validate_config(config):
        if not config.c.has_section('awsevents'):
            print('no [awsevents] config section')
            sys.exit(1)

    return run_cli('snsconsumer', on_event, validate_config=validate_config)
