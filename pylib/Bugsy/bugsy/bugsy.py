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

    DEFAULT_SEARCH = ['version', 'id', 'summary', 'status', 'op_sys',
                      'resolution', 'product', 'component', 'platform',
                      'whiteboard']

    def __init__(
            self,
            username=None,
            password=None,
            userid=None,
            cookie=None,
            api_key=None,
            bugzilla_url='https://bugzilla.mozilla.org/rest'
    ):
        """
            Initialises a new instance of Bugsy

            :param username: Username to login with. Defaults to None
            :param password: Password to login with. Defaults to None
            :param userid: User ID to login with. Defaults to None
            :param cookie: Cookie to login with. Defaults to None
            :param apikey: API key to use. Defaults to None.
            :param bugzilla_url: URL endpoint to interact with. Defaults to
            https://bugzilla.mozilla.org/rest

            If a api_key is passed in, Bugsy will use this for authenticating
            requests. While not required to perform requests, if a username is
            passed in along with api_key, we will validate that the api key is
            valid for this username. Otherwise the api key is blindly used
            later.

            If a username AND password are passed in Bugsy will try get a login
            token from Bugzilla. If we can't login then a LoginException will
            be raised.

            If a userid AND cookie are passed in Bugsy will create a login
            token from them.
            If no username was passed in it will then try to get the username
            from Bugzilla.
        """
        self.api_key = api_key
        self.username = username
        self.password = password
        self.userid = userid
        self.cookie = cookie
        self.bugzilla_url = bugzilla_url
        self.token = None
        self.session = requests.Session()
        self._have_auth = False

        # Prefer API keys over all other auth methods.
        if self.api_key:
            if self.username:
                result = self.request(
                    'valid_login',
                    params={'login': username, 'api_key': api_key}
                )

                if result.json() is not True:
                    raise LoginException(result.json()['message'])

            self.session.params['api_key'] = self.api_key
            self._have_auth = True
        elif self.username and self.password:
            result = self.request(
                'login',
                params={'login': username, 'password': password}
            )
            result = result.json()
            if 'token' in result:
                self.session.params['token'] = result['token']
                self.token = result['token']
            else:
                raise LoginException(result['message'])
            self._have_auth = True
        elif self.userid and self.cookie:
            # The token is crafted from the userid and cookie.
            self.token = '%s-%s' % (self.userid, self.cookie)
            self.session.params['token'] = self.token
            if not self.username:
                result = self.request('user/%s' % self.userid).json()
                if result.get('users', []):
                    self.username = result['users'][0]['name']
                else:
                    raise LoginException(result['message'])

            self._have_auth = True

    def get(self, bug_number):
        """
            Get a bug from Bugzilla. If there is a login token created during
            object initialisation it will be part of the query string passed to
            Bugzilla

            :param bug_number: Bug Number that will be searched. If found will
                               return a Bug object.

            >>> bugzilla = Bugsy()
            >>> bug = bugzilla.get(123456)
        """
        bug = self.request(
            'bug/%s' % bug_number,
            params={"include_fields": self. DEFAULT_SEARCH}
        ).json()
        return Bug(self, **bug['bugs'][0])

    def put(self, bug):
        """
            This method allows you to create or update a bug on Bugzilla. You
            will have had to pass in a valid username and password to the
            object initialisation and recieved back a token.

            :param bug: A Bug object either created by hand or by using get()

            If there is no valid token then a BugsyException will be raised.
            If the object passed in is not a Bug then a BugsyException will
            be raised.

            >>> bugzilla = Bugsy()
            >>> bug = bugzilla.get(123456)
            >>> bug.summary = "I like cheese and sausages"
            >>> bugzilla.put(bug)

        """
        if not self._have_auth:
            raise BugsyException("Unfortunately you can't put bugs in Bugzilla"
                                 " without credentials")

        if not isinstance(bug, Bug):
            raise BugsyException("Please pass in a Bug object when posting"
                                 " to Bugzilla")

        if not bug.id:
            result = self.request('bug', 'POST', data=bug.to_dict()).json()
            if 'error' not in result:
                bug._bug['id'] = result['id']
                bug._bugsy = self
            else:
                raise BugsyException(result['message'])
        else:
            result = self.request('bug/%s' % bug.id, 'PUT',
                                  data=bug.to_dict()).json()
            if "error" in result:
                raise BugsyException(result['message'])

    @property
    def search_for(self):
        return Search(self)

    def request(self, path, method='GET', **kwargs):
        """Perform a HTTP request.

        Given a relative Bugzilla URL path, an optional request method,
        and arguments suitable for requests.Request(), perform a
        HTTP request.
        """
        headers = {"User-Agent": "Bugsy"}
        kwargs['headers'] = headers
        url = '%s/%s' % (self.bugzilla_url, path)
        return self.session.request(method, url, **kwargs)
