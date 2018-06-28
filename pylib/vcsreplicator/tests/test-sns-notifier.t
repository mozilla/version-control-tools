#require hgmodocker vcsreplicator

  $ . $TESTDIR/pylib/vcsreplicator/tests/helpers.sh
  $ vcsrenv
  $ standarduser

We don't create the SNS topic on the moto server automatically. Do that
here.

  $ hgmo exec hgssh /configure-events-servers
  snsnotifier: stopped
  snsnotifier: started
  created S3 bucket moz-hg-events-us-west-2
  created SNS topic hgmo-events (arn:aws:sns:us-east-1:123456789012:hgmo-events)

Create some repositories

  $ hgmo create-repo mozilla-central scm_level_1
  (recorded repository creation in replication log)

  $ hgmo exec hgweb0 /var/hg/venv_replication/bin/vcsreplicator-consumer --wait-for-no-lag /etc/mercurial/vcsreplicator.ini
  $ hgmo exec hgweb1 /var/hg/venv_replication/bin/vcsreplicator-consumer --wait-for-no-lag /etc/mercurial/vcsreplicator.ini

  $ hgmo create-repo try scm_level_1
  (recorded repository creation in replication log)

  $ hgmo exec hgweb0 /var/hg/venv_replication/bin/vcsreplicator-consumer --wait-for-no-lag /etc/mercurial/vcsreplicator.ini
  $ hgmo exec hgweb1 /var/hg/venv_replication/bin/vcsreplicator-consumer --wait-for-no-lag /etc/mercurial/vcsreplicator.ini

  $ hgmo exec hgssh /set-hgrc-option mozilla-central phases publish false
  $ hgmo exec hgssh /set-hgrc-option mozilla-central experimental evolution all
  $ hgmo exec hgssh /var/hg/venv_pash/bin/hg -R /repo/hg/mozilla/mozilla-central replicatehgrc
  recorded hgrc in replication log

Changegroup message works

  $ hg -q clone ssh://${SSH_SERVER}:${SSH_PORT}/mozilla-central
  $ cd mozilla-central
  $ touch foo
  $ hg -q commit -A -m initial
  $ hg phase --public -r .
  $ hg -q push

Create an obsolete changeset with a large commit message to test SNS message size limits

  $ cat >> .hg/hgrc << EOF
  > [extensions]
  > rebase =
  > [experimental]
  > evolution = all
  > EOF

  $ echo orig > foo
  >>> with open('message', 'wb') as fh:
  ...     fh.write('this is a long commit message\n')
  ...     fh.write('\n')
  ...     fh.write('a' * 259800)
  $ hg commit -l message

  $ hg -q push
  $ hg commit --amend -m 'rewritten message'
  $ hg -q push

Without this, there is a race condition in the order that the aggregator may
process acknowledged messages across partitions

  $ hgmo exec hgweb0 /var/hg/venv_replication/bin/vcsreplicator-consumer --wait-for-no-lag /etc/mercurial/vcsreplicator.ini
  $ hgmo exec hgweb1 /var/hg/venv_replication/bin/vcsreplicator-consumer --wait-for-no-lag /etc/mercurial/vcsreplicator.ini

An SNS message should be sent with the event details

  $ paconsumer --wait-for-n 18
  got a heartbeat-1 message
  got a hg-repo-init-2 message
  got a heartbeat-1 message
  got a hg-repo-init-2 message
  got a hg-hgrc-update-1 message
  got a heartbeat-1 message
  got a heartbeat-1 message
  got a hg-changegroup-2 message
  got a hg-heads-1 message
  got a heartbeat-1 message
  got a heartbeat-1 message
  got a hg-changegroup-2 message
  got a hg-heads-1 message
  got a heartbeat-1 message
  got a heartbeat-1 message
  got a hg-changegroup-2 message
  got a hg-pushkey-1 message
  got a hg-heads-1 message

  $ snsconsumer --wait-for-no-lag

  $ hgmo exec hgssh tail -n 42 /var/log/snsnotifier.log
  vcsreplicator.pushnotifications heartbeat-1 message not relevant; ignoring
  vcsreplicator.snsnotifier processing message 1: newrepo.1 for https://hg.mozilla.org/mozilla-central
  vcsreplicator.snsnotifier uploading to S3: http://localhost:5001/moz-hg-events-us-west-2/events/*/0000000001-*.json (glob)
  vcsreplicator.snsnotifier sending SNS notification to arn:aws:sns:us-east-1:123456789012:hgmo-events
  vcsreplicator.snsnotifier finished processing message 1
  vcsreplicator.pushnotifications heartbeat-1 message not relevant; ignoring
  vcsreplicator.snsnotifier processing message 3: newrepo.1 for https://hg.mozilla.org/try
  vcsreplicator.snsnotifier uploading to S3: http://localhost:5001/moz-hg-events-us-west-2/events/*/0000000003-*.json (glob)
  vcsreplicator.snsnotifier sending SNS notification to arn:aws:sns:us-east-1:123456789012:hgmo-events
  vcsreplicator.snsnotifier finished processing message 3
  vcsreplicator.pushnotifications hg-hgrc-update-1 message not relevant to push notifier; ignoring
  vcsreplicator.pushnotifications heartbeat-1 message not relevant; ignoring
  vcsreplicator.pushnotifications heartbeat-1 message not relevant; ignoring
  vcsreplicator.pushnotifications querying pushlog data for /repo/hg/mozilla/mozilla-central
  vcsreplicator.snsnotifier processing message 7: changegroup.1 for https://hg.mozilla.org/mozilla-central
  vcsreplicator.snsnotifier uploading to S3: http://localhost:5001/moz-hg-events-us-west-2/events/*/0000000007-*.json (glob)
  vcsreplicator.snsnotifier sending SNS notification to arn:aws:sns:us-east-1:123456789012:hgmo-events
  vcsreplicator.snsnotifier finished processing message 7
  vcsreplicator.pushnotifications hg-heads-1 message not relevant to push notifier; ignoring
  vcsreplicator.pushnotifications heartbeat-1 message not relevant; ignoring
  vcsreplicator.pushnotifications heartbeat-1 message not relevant; ignoring
  vcsreplicator.pushnotifications querying pushlog data for /repo/hg/mozilla/mozilla-central
  vcsreplicator.snsnotifier processing message 11: changegroup.1 for https://hg.mozilla.org/mozilla-central
  vcsreplicator.snsnotifier uploading to S3: http://localhost:5001/moz-hg-events-us-west-2/events/*/0000000011-*.json (glob)
  vcsreplicator.snsnotifier sending SNS notification to arn:aws:sns:us-east-1:123456789012:hgmo-events
  vcsreplicator.snsnotifier finished processing message 11
  vcsreplicator.pushnotifications hg-heads-1 message not relevant to push notifier; ignoring
  vcsreplicator.pushnotifications heartbeat-1 message not relevant; ignoring
  vcsreplicator.pushnotifications heartbeat-1 message not relevant; ignoring
  vcsreplicator.pushnotifications querying pushlog data for /repo/hg/mozilla/mozilla-central
  vcsreplicator.snsnotifier processing message 15: changegroup.1 for https://hg.mozilla.org/mozilla-central
  vcsreplicator.snsnotifier uploading to S3: http://localhost:5001/moz-hg-events-us-west-2/events/*/0000000015-*.json (glob)
  vcsreplicator.snsnotifier sending SNS notification to arn:aws:sns:us-east-1:123456789012:hgmo-events
  vcsreplicator.snsnotifier finished processing message 15
  vcsreplicator.pushnotifications processing obsolete pushkey message for https://hg.mozilla.org/mozilla-central
  vcsreplicator.pushnotifications processing 1 obsolete markers
  vcsreplicator.snsnotifier processing message 16: obsolete.1 for https://hg.mozilla.org/mozilla-central
  vcsreplicator.snsnotifier message too large for SNS; dropping payload
  vcsreplicator.snsnotifier uploading to S3: http://localhost:5001/moz-hg-events-us-west-2/events/*/0000000016-*.json (glob)
  vcsreplicator.snsnotifier sending SNS notification to arn:aws:sns:us-east-1:123456789012:hgmo-events
  vcsreplicator.snsnotifier finished processing message 16
  vcsreplicator.pushnotifications hg-heads-1 message not relevant to push notifier; ignoring

  $ hgmo exec hgssh cat /sns-messages
  POST /hgmo-events {
      "Message": [
          "{\"data\": {\"repo_url\": \"https://hg.mozilla.org/mozilla-central\"}, \"data_url\": \"http://localhost:5001/moz-hg-events-us-west-2/events/*/0000000001-*.json\", \"type\": \"newrepo.1\"}" (glob)
      ],
      "MessageId": [
          "*" (glob)
      ],
      "Signature": [
          "EXAMPLElDMXvB8r9R83tGoNn0ecwd5UjllzsvSvbItzfaMpN2nk5HVSw7XnOn/49IkxDKz8YrlH2qJXj2iZB0Zo2O71c4qQk1fMUDi3LGpij7RCW7AW9vYYsSqIKRnFS94ilu7NFhUzLiieYr4BKHpdTmdD6c0esKEYBpabxDSc="
      ],
      "SignatureVersion": [
          "1"
      ],
      "SigningCertURL": [
          "https://sns.us-east-1.amazonaws.com/SimpleNotificationService-f3ecfb7224c7233fe7bb5f59f96de52f.pem"
      ],
      "Subject": [
          "my subject"
      ],
      "Timestamp": [
          "*T*Z" (glob)
      ],
      "TopicArn": [
          "arn:aws:sns:us-east-1:123456789012:hgmo-events"
      ],
      "Type": [
          "Notification"
      ],
      "UnsubscribeURL": [
          "https://sns.us-east-1.amazonaws.com/?Action=Unsubscribe&SubscriptionArn=arn:aws:sns:us-east-1:123456789012:some-topic:2bcfbf39-05c3-41de-beaa-fcfcc21c8f55"
      ]
  }
  POST /hgmo-events {
      "Message": [
          "{\"data\": {\"repo_url\": \"https://hg.mozilla.org/try\"}, \"data_url\": \"http://localhost:5001/moz-hg-events-us-west-2/events/*/0000000003-*.json\", \"type\": \"newrepo.1\"}" (glob)
      ],
      "MessageId": [
          "*" (glob)
      ],
      "Signature": [
          "EXAMPLElDMXvB8r9R83tGoNn0ecwd5UjllzsvSvbItzfaMpN2nk5HVSw7XnOn/49IkxDKz8YrlH2qJXj2iZB0Zo2O71c4qQk1fMUDi3LGpij7RCW7AW9vYYsSqIKRnFS94ilu7NFhUzLiieYr4BKHpdTmdD6c0esKEYBpabxDSc="
      ],
      "SignatureVersion": [
          "1"
      ],
      "SigningCertURL": [
          "https://sns.us-east-1.amazonaws.com/SimpleNotificationService-f3ecfb7224c7233fe7bb5f59f96de52f.pem"
      ],
      "Subject": [
          "my subject"
      ],
      "Timestamp": [
          "*" (glob)
      ],
      "TopicArn": [
          "arn:aws:sns:us-east-1:123456789012:hgmo-events"
      ],
      "Type": [
          "Notification"
      ],
      "UnsubscribeURL": [
          "https://sns.us-east-1.amazonaws.com/?Action=Unsubscribe&SubscriptionArn=arn:aws:sns:us-east-1:123456789012:some-topic:2bcfbf39-05c3-41de-beaa-fcfcc21c8f55"
      ]
  }
  POST /hgmo-events {
      "Message": [
          "{\"data\": {\"heads\": [\"77538e1ce4bec5f7aac58a7ceca2da0e38e90a72\"], \"pushlog_pushes\": [{\"push_full_json_url\": \"https://hg.mozilla.org/mozilla-central/json-pushes?version=2&full=1&startID=0&endID=1\", \"push_json_url\": \"https://hg.mozilla.org/mozilla-central/json-pushes?version=2&startID=0&endID=1\", \"pushid\": 1, \"time\": *, \"user\": \"user@example.com\"}], \"repo_url\": \"https://hg.mozilla.org/mozilla-central\", \"source\": \"serve\"}, \"data_url\": \"http://localhost:5001/moz-hg-events-us-west-2/events/*/0000000007-*.json\", \"type\": \"changegroup.1\"}" (glob)
      ],
      "MessageId": [
          "*" (glob)
      ],
      "Signature": [
          "EXAMPLElDMXvB8r9R83tGoNn0ecwd5UjllzsvSvbItzfaMpN2nk5HVSw7XnOn/49IkxDKz8YrlH2qJXj2iZB0Zo2O71c4qQk1fMUDi3LGpij7RCW7AW9vYYsSqIKRnFS94ilu7NFhUzLiieYr4BKHpdTmdD6c0esKEYBpabxDSc="
      ],
      "SignatureVersion": [
          "1"
      ],
      "SigningCertURL": [
          "https://sns.us-east-1.amazonaws.com/SimpleNotificationService-f3ecfb7224c7233fe7bb5f59f96de52f.pem"
      ],
      "Subject": [
          "my subject"
      ],
      "Timestamp": [
          "*" (glob)
      ],
      "TopicArn": [
          "arn:aws:sns:us-east-1:123456789012:hgmo-events"
      ],
      "Type": [
          "Notification"
      ],
      "UnsubscribeURL": [
          "https://sns.us-east-1.amazonaws.com/?Action=Unsubscribe&SubscriptionArn=arn:aws:sns:us-east-1:123456789012:some-topic:2bcfbf39-05c3-41de-beaa-fcfcc21c8f55"
      ]
  }
  POST /hgmo-events {
      "Message": [
          "{\"data\": {\"heads\": [\"2971b4149fdfe8541e8ddddd0a2dce39b90f5e70\"], \"pushlog_pushes\": [{\"push_full_json_url\": \"https://hg.mozilla.org/mozilla-central/json-pushes?version=2&full=1&startID=1&endID=2\", \"push_json_url\": \"https://hg.mozilla.org/mozilla-central/json-pushes?version=2&startID=1&endID=2\", \"pushid\": 2, \"time\": *, \"user\": \"user@example.com\"}], \"repo_url\": \"https://hg.mozilla.org/mozilla-central\", \"source\": \"serve\"}, \"data_url\": \"http://localhost:5001/moz-hg-events-us-west-2/events/*/0000000011-*.json\", \"type\": \"changegroup.1\"}" (glob)
      ],
      "MessageId": [
          "*" (glob)
      ],
      "Signature": [
          "EXAMPLElDMXvB8r9R83tGoNn0ecwd5UjllzsvSvbItzfaMpN2nk5HVSw7XnOn/49IkxDKz8YrlH2qJXj2iZB0Zo2O71c4qQk1fMUDi3LGpij7RCW7AW9vYYsSqIKRnFS94ilu7NFhUzLiieYr4BKHpdTmdD6c0esKEYBpabxDSc="
      ],
      "SignatureVersion": [
          "1"
      ],
      "SigningCertURL": [
          "https://sns.us-east-1.amazonaws.com/SimpleNotificationService-f3ecfb7224c7233fe7bb5f59f96de52f.pem"
      ],
      "Subject": [
          "my subject"
      ],
      "Timestamp": [
          "*" (glob)
      ],
      "TopicArn": [
          "arn:aws:sns:us-east-1:123456789012:hgmo-events"
      ],
      "Type": [
          "Notification"
      ],
      "UnsubscribeURL": [
          "https://sns.us-east-1.amazonaws.com/?Action=Unsubscribe&SubscriptionArn=arn:aws:sns:us-east-1:123456789012:some-topic:2bcfbf39-05c3-41de-beaa-fcfcc21c8f55"
      ]
  }
  POST /hgmo-events {
      "Message": [
          "{\"data\": {\"heads\": [\"76bf70283ec77e25c4ce99d27dccc12d6ede5837\"], \"pushlog_pushes\": [{\"push_full_json_url\": \"https://hg.mozilla.org/mozilla-central/json-pushes?version=2&full=1&startID=2&endID=3\", \"push_json_url\": \"https://hg.mozilla.org/mozilla-central/json-pushes?version=2&startID=2&endID=3\", \"pushid\": 3, \"time\": *, \"user\": \"user@example.com\"}], \"repo_url\": \"https://hg.mozilla.org/mozilla-central\", \"source\": \"serve\"}, \"data_url\": \"http://localhost:5001/moz-hg-events-us-west-2/events/*/0000000015-*.json\", \"type\": \"changegroup.1\"}" (glob)
      ],
      "MessageId": [
          "*" (glob)
      ],
      "Signature": [
          "EXAMPLElDMXvB8r9R83tGoNn0ecwd5UjllzsvSvbItzfaMpN2nk5HVSw7XnOn/49IkxDKz8YrlH2qJXj2iZB0Zo2O71c4qQk1fMUDi3LGpij7RCW7AW9vYYsSqIKRnFS94ilu7NFhUzLiieYr4BKHpdTmdD6c0esKEYBpabxDSc="
      ],
      "SignatureVersion": [
          "1"
      ],
      "SigningCertURL": [
          "https://sns.us-east-1.amazonaws.com/SimpleNotificationService-f3ecfb7224c7233fe7bb5f59f96de52f.pem"
      ],
      "Subject": [
          "my subject"
      ],
      "Timestamp": [
          "*" (glob)
      ],
      "TopicArn": [
          "arn:aws:sns:us-east-1:123456789012:hgmo-events"
      ],
      "Type": [
          "Notification"
      ],
      "UnsubscribeURL": [
          "https://sns.us-east-1.amazonaws.com/?Action=Unsubscribe&SubscriptionArn=arn:aws:sns:us-east-1:123456789012:some-topic:2bcfbf39-05c3-41de-beaa-fcfcc21c8f55"
      ]
  }
  POST /hgmo-events {
      "Message": [
          "{\"data_url\": \"http://localhost:5001/moz-hg-events-us-west-2/events/*/0000000016-*.json\", \"external\": true, \"repo_url\": \"https://hg.mozilla.org/mozilla-central\", \"type\": \"obsolete.1\"}" (glob)
      ],
      "MessageId": [
          "*" (glob)
      ],
      "Signature": [
          "EXAMPLElDMXvB8r9R83tGoNn0ecwd5UjllzsvSvbItzfaMpN2nk5HVSw7XnOn/49IkxDKz8YrlH2qJXj2iZB0Zo2O71c4qQk1fMUDi3LGpij7RCW7AW9vYYsSqIKRnFS94ilu7NFhUzLiieYr4BKHpdTmdD6c0esKEYBpabxDSc="
      ],
      "SignatureVersion": [
          "1"
      ],
      "SigningCertURL": [
          "https://sns.us-east-1.amazonaws.com/SimpleNotificationService-f3ecfb7224c7233fe7bb5f59f96de52f.pem"
      ],
      "Subject": [
          "my subject"
      ],
      "Timestamp": [
          "*" (glob)
      ],
      "TopicArn": [
          "arn:aws:sns:us-east-1:123456789012:hgmo-events"
      ],
      "Type": [
          "Notification"
      ],
      "UnsubscribeURL": [
          "https://sns.us-east-1.amazonaws.com/?Action=Unsubscribe&SubscriptionArn=arn:aws:sns:us-east-1:123456789012:some-topic:2bcfbf39-05c3-41de-beaa-fcfcc21c8f55"
      ]
  }

Cleanup

  $ hgmo clean
