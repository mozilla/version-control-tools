# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

# This Lambda function takes GitHub web hook events and sends them to
# Firehose and SNS. Firehose takes care of long-term retention in S3.
# SNS is used to trigger other Lambda functions.
#
# Ideally, these would be separate Lambda functions. However, since
# GitHub web hooks are ingested by an API Gateway and since you can
# only have 1 Lambda per HTTP endpoint+method, our hands are tied.

import boto3
import json


# Set of events that we consider public.
#
# We don't publish all events because some events contain information that
# is private/confidential and/or is related to the operational configuration
# of repositories or organizations.
#
# We explicitly list events that will be published to prevent unwanted
# disclosure of data from new event types.
PUBLIC_EVENTS = {
    'commit_comment',
    'create', # branch or tag created
    'delete', # branch or tag deleted
    'deployment',
    'deployment_status',
    'fork',
    'gollum', # wiki page update
    'issue_comment',
    'issues',
    # We don't publish membership changes because those are semi-private.
    # 'member', # user added as collaborator
    # 'membership', # team membership changed
    'page_build',
    # We don't republish this to lessen the chances that accidental repo
    # publication will result in consumers grabbing its content.
    # 'public', # repo changes from private to public
    'pull_request_review_comment',
    'pull_request_review',
    'pull_request',
    'push',
    # There are privacy and security implications with publishing repo changes.
    # 'repository',
    'release',
    'status',
    # Again, membership isn't relevant to the public.
    # 'team_add',
    'watch',
}



firehose = boto3.client('firehose')
sns = boto3.client('sns')


def handler(event, context):
    if 'params' not in event:
        raise Exception('event payload does not match expected; are you using the API gateway?')

    event_name = event['params']['header']['X-GitHub-Event']

    data = json.dumps({
        'event': event_name,
        'request_id': event['params']['header']['X-GitHub-Delivery'],
        'body': event['body-json'],
    }, sort_keys=True)

    print('sending to firehose')
    firehose.put_record(
        DeliveryStreamName='github-webhooks',
        Record={'Data': data},
    )

    print('sending to github-webhooks-all SNS')
    sns.publish(
        TopicArn='arn:aws:sns:us-west-2:699292812394:github-webhooks-all',
        Message=data,
    )

    if event_name not in PUBLIC_EVENTS:
        print('not publishing to public channel because event %s is not allowed' % event_name)
    elif event['body-json']['repository']['private']:
        print('not publishing to public channel because repo is private')
    else:
        print('sending to github-webhooks-public SNS')
        sns.publish(
            TopicArn='arn:aws:sns:us-west-2:699292812394:github-webhooks-public',
            Message=data,
        )
