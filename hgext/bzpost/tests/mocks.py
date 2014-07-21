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

bug123comment = {
    'bugs': {
        '123': {
            'comments': [
                {
                   'attachment_id': None,
                   'author': 'gps@mozilla.com',
                   'bug_id': 1017315,
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

responses.add(responses.GET, bzurl + '/bug/123/comment?token=foobar',
        body=json.dumps(bug123comment),
        status=200,
        content_type='application/json',
        match_querystring=True)

responses.add(responses.POST, bzurl + '/bug/123/comment?token=foobar',
        body='{}',
        status=200,
        content_type='application/json',
        match_querystring=True)
