import json
import requests
import unittest

class TestAutolandIntegration(unittest.TestCase):


    def test_root(self):
        """Test getting /"""

        r = requests.get('http://localhost:8000/')
        self.assertEqual(r.status_code, 200, 'Get / should return 200')
        self.assertEqual(r.text, 'Welcome to Autoland')


    def test_autoland_post(self):
        """Test posting a request to the /autoland endpoint"""

        data = {
            'tree': 'mozilla-central',
            'rev': '2bcb4d148ef5',
            'destination': 'try',
            'trysyntax': 'try: -b o -p linux -u mochitest-1 -t none',
            'endpoint': 'http://localhost:8000'
        }

        r = requests.post('http://localhost:8000/autoland',
                          data=json.dumps(data),
                          headers= {'Content-Type': 'application/json'},
                          auth=('autoland', 'autoland'))

        self.assertEqual(r.status_code, 200,
                         'Post to autoland should return 200')
        self.assertTrue('request_id' in json.loads(r.text),
                        'Response should contain request_id')

        r = requests.delete('http://localhost:8000/autoland')
        self.assertEqual(r.status_code, 405,
                         'Get to autoland should return 405')

        r = requests.get('http://localhost:8000/autoland')
        self.assertEqual(r.status_code, 404,
                         'Get to autoland should return 404')

        r = requests.put('http://localhost:8000/autoland',
                         data=json.dumps(data),
                         headers= {'Content-Type': 'application/json'})
        self.assertEqual(r.status_code, 405,
                         'Put to autoland should return 405')

        r = requests.post('http://localhost:8000/autoland',
                          data=json.dumps(data),
                          headers= {'Content-Type': 'application/json'})
        self.assertEqual(r.status_code, 401,
                         'Post with no auth should return 401')

        r = requests.post('http://localhost:8000/autoland',
                          data=json.dumps(data),
                          headers= {'Content-Type': 'application/json'},
                          auth=('autolnd', 'autoland'))
        self.assertEqual(r.status_code, 401,
                         'Post with bad user should return 401')

        r = requests.post('http://localhost:8000/autoland',
                          data=json.dumps(data),
                          headers= {'Content-Type': 'application/json'},
                          auth=('autoland', 'autolnd'))
        self.assertEqual(r.status_code, 401,
                         'Post with bad paswd should return 401')

        r = requests.post('http://localhost:8000/autoland',
                          headers= {'Content-Type': 'application/json'},
                          auth=('autoland', 'autoland'))

        self.assertEqual(r.status_code, 400, 'Missing data should return 400')

        data = {
            'tree': 'mozilla-central',
            'rev': '2bcb4d148ef5',
            'destination': 'try',
            'endpoint': 'http://localhost:8000'
        }

        r = requests.post('http://localhost:8000/autoland',
                          data=json.dumps(data),
                          headers= {'Content-Type': 'application/json'},
                          auth=('autoland', 'autoland'))

        self.assertEqual(r.status_code, 200,
                         'Trysyntax should be optional')

        r = requests.post('http://localhost:8000/autoland',
                          data=json.dumps({}),
                          headers= {'Content-Type': 'application/json'},
                          auth=('autoland', 'autoland'))

        self.assertEqual(r.status_code, 400,
                         'Empty data should return bad request')


    def test_autoland_status_endpoint(self):
        """Test getting status from the /autoland/status/ endpoint"""

        data = {
            'tree': 'mozilla-central',
            'rev': '2bcb4d148ef5',
            'destination': 'try',
            'trysyntax': 'try: -b o -p linux -u mochitest-1 -t none',
            'endpoint': 'http://localhost:8000'
        }

        r = requests.post('http://localhost:8000/autoland',
                          data=json.dumps(data),
                          headers= {'Content-Type': 'application/json'},
                          auth=('autoland', 'autoland'))

        self.assertEqual(r.status_code, 200,
                         'Post to autoland should return 200')

        req_id = json.loads(r.text)['request_id']

        r = requests.get('http://localhost:8000/autoland/status/' + str(req_id))
        self.assertEqual(r.status_code, 200,
                         'Get autoland status should return 200')

        status = json.loads(r.text)
        self.assertIsNotNone(status, 'Get autoland status should return json')

        for key in data:
            self.assertEqual(data[key], status[key],
                             '%s in status should match posted data')

        self.assertTrue('landed' in status)
        self.assertTrue('result' in status)

        r = requests.get('http://localhost:8000/autoland/status/wtf')
        self.assertEqual(r.status_code, 404,
                         'Unknown job should return 404')


    def test_bad_url(self):

        urls = ['/adflkj',
                '/adslkfjadf/adflkjadf',
                '/aldskfj/aldfkj/3298023/adlfkja/dalfj']

        for url in urls:
            r = requests.get('http://localhost:8000' + url)
            self.assertEqual(r.status_code, 404,
                             'Url %s should return 404' % url)


if __name__ == '__main__':
    unittest.main()
