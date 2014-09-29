import copy
import json

responses.add(responses.GET, bzurl + '/login?login=bzpost&password=pass',
        body='{"token": "foobar"}',
        status=200,
        content_type='application/json',
        match_querystring=True)

bug123 = {
    'faults': [],
    'bugs': [{
        'id': 123,
    }],
}

responses.add(responses.GET, bzurl + '/bug/123',
        body=json.dumps(bug123),
        status=200,
        content_type='application/json')

bug124 = {
    'faults': [],
    'bugs': [{
        'id': 124,
    }],
}

responses.add(responses.GET, bzurl + '/bug/124',
        body=json.dumps(bug124),
        status=200,
        content_type='application/json')

bug123comment = {
    'bugs': {
        '123': {
            'comments': [
                {
                   'attachment_id': None,
                   'author': 'gps@mozilla.com',
                   'bug_id': 123,
                   'creation_time': '2014-03-27T23:47:45Z',
                   'creator': 'gps@mozilla.com',
                   'id': 8589785,
                   'is_private': False,
                   'raw_text': 'raw text 1',
                   'tags': ['tag1', 'tag2'],
                   'text': 'text 1',
                   'time': '2014-03-27T23:47:45Z'
                },
            ],
        },
    },
}

bug124comment = {
    'bugs': {
        '124': copy.deepcopy(bug123comment['bugs']['123']),
    },
}
bug124comment['bugs']['124']['comments'][0]['bug_id'] = 124,

responses.add(responses.GET, bzurl + '/bug/123/comment?token=foobar',
        body=json.dumps(bug123comment),
        status=200,
        content_type='application/json',
        match_querystring=True)

responses.add(responses.GET, bzurl + '/bug/124/comment?token=foobar',
        body=json.dumps(bug124comment),
        status=200,
        content_type='application/json',
        match_querystring=True)

for bug in ('123', '124'):
    responses.add(responses.POST, bzurl + '/bug/%s/comment?token=foobar' % bug,
            body='{}',
            status=200,
            content_type='application/json',
            match_querystring=True)
