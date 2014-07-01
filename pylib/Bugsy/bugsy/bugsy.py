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
        self.token = None
        self.bugzilla_url = bugzilla_url
        if self.username and self.password:
            result = requests.get(bugzilla_url + '/login?login=%s&password=%s' % (self.username, self.password)).json()
            if result.has_key('token'):
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
        url = self.bugzilla_url + "/bug/%s" % bug_number
        if self.token:
            url = url + "?token=%s" % self.token

        bug = requests.get(url).json()
        return Bug(self.bugzilla_url, self.token, **bug['bugs'][0])

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
            result = requests.post(self.bugzilla_url + "/bug?token=%s" % self.token, bug.to_dict()).json()
            if not result.has_key('error'):
                bug._bug['id'] = result['id']
            else:
                raise BugsyException(result['message'])
        else:
            requests.post(self.bugzilla_url + "/bug/%s?token=%s" % (bug.id, self.token), bug.to_dict())

    def search_for():
        doc = "The search_for property."
        def fget(self):
            return Search(self.bugzilla_url, self.token)
        return locals()
    search_for = property(**search_for())

