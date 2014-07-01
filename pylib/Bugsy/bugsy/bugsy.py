import json

import requests
from bug import Bug
from search import Search


class BugsyException(Exception):
    """
        If while interacting with Bugzilla and we try do something that is not
        supported this error will be raised.
    """
    def __init__(self, msg):
        self.msg = msg

    def __str__(self):
        return "Message: %s" % self.msg

class LoginException(Exception):
    """
        If a username and password are passed in but we don't receive a token
        then this error will be raised.
    """
    def __init__(self, msg):
        self.msg = msg

    def __str__(self):
        return "Message: %s" % self.msg

class Bugsy(object):
    """
        Bugsy allows easy getting and putting of Bugzilla bugs
    """

    def __init__(self, username=None, password=None, bugzilla_url='https://bugzilla.mozilla.org/rest'):
        """
            Initialises a new instance of Bugsy

            :param username: Username to login with. Defaults to None
            :param password: Password to login with. Defaults to None
            :param bugzilla_url: URL endpoint to interact with. Defaults to https://bugzilla.mozilla.org/rest

            If a username AND password are passed in Bugsy will try get a login token
            from Bugzilla. If we can't login then a LoginException will
            be raised.
        """
        self.username = username
        self.password = password
        self.bugzilla_url = bugzilla_url
        self.token = None
        self.session = requests.Session()

        if self.username and self.password:
            result = self.request('login',
                params={'login': username, 'password': password})
            result = result.json()
            if result.has_key('token'):
                self.session.params['token'] = result['token']
                self.token = result['token']
            else:
                raise LoginException(result['message'])

    def get(self, bug_number):
        """
            Get a bug from Bugzilla. If there is a login token created during object initialisation
            it will be part of the query string passed to Bugzilla

            :param bug_number: Bug Number that will be searched. If found will return a Bug object.

            >>> bugzilla = Bugsy()
            >>> bug = bugzilla.get(123456)
        """
        bug = self.request('bug/%s' % bug_number).json()
        return Bug(self, **bug['bugs'][0])

    def put(self, bug):
        """
            This method allows you to create or update a bug on Bugzilla. You will have had to pass
            in a valid username and password to the object initialisation and recieved back a token.

            :param bug: A Bug object either created by hand or by using get()

            If there is no valid token then a BugsyException will be raised.
            If the object passed in is not a Bug then a BugsyException will be raised.

            >>> bugzilla = Bugsy()
            >>> bug = bugzilla.get(123456)
            >>> bug.summary = "I like cheese and sausages"
            >>> bugzilla.put(bug)

        """
        if not self.token:
            raise BugsyException("Unfortunately you can't put bugs in Bugzilla without credentials")

        if not isinstance(bug, Bug):
            raise BugsyException("Please pass in a Bug object when posting to Bugzilla")

        if not bug.id:
            result = self.request('bug', 'POST', data=bug.to_dict()).json()
            if not result.has_key('error'):
                bug._bug['id'] = result['id']
            else:
                raise BugsyException(result['message'])
        else:
            self.session.post('%s/bug/%s' % (self.bugzilla_url, bug.id),
                data=bug.to_dict())

    def search_for():
        doc = "The search_for property."
        def fget(self):
            return Search(self)
        return locals()
    search_for = property(**search_for())

    def request(self, path, method='GET', **kwargs):
        """Perform a HTTP request.

        Given a relative Bugzilla URL path, an optional request method,
        and arguments suitable for requests.Request(), perform a
        HTTP request.
        """
        url = '%s/%s' % (self.bugzilla_url, path)
        return self.session.request(method, url, **kwargs)

