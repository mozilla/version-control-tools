import config
import requests
import urlparse

API_KEY_LOGIN_PATH = ('/api/extensions/mozreview.extension.MozReviewExtension/'
                      'bugzilla-api-key-logins/')

# Requires a 'bugzilla' object in config.json.
#
# For user/api-key authentication (preferred):
#   "bugzilla": {
#       "user": "level1@example.com",
#       "api-key": "znqzPYGqAoWrMbm88bmTbhg6KQUV4SdtW8T9VucX"
#   }
#
# For user/password authentication:
#   "bugzilla": {
#       "user": "level1@example.com",
#       "passwd": "password",
#   }

class BugzillaAuthException(Exception):
    pass


class BugzillaAuth(object):
    """Base class for authentication."""

    _config = None

    def __init__(self, bugzilla_config):
        self._config = bugzilla_config

    def headers(self, pingback_url):
        """HTTP headers to include in the pingback post."""
        return {'Content-Type': 'application/json'}

    def http_auth(self):
        """Basic HTTP auth credentials, as user/pass tuple."""
        return None


class BugzillaAuthPassword(BugzillaAuth):
    """Username/password authentication.  Used in dev and test."""

    def http_auth(self):
        return self._config['user'], self._config['passwd']


class BugzillaAuthApiKey(BugzillaAuth):
    """Username/API-Key authentication."""

    _cookies = {}

    def headers(self, pingback_url):
        """Track cookies for each Review Board instance."""
        url = urlparse.urlparse(pingback_url)
        host = url.netloc

        if host not in self._cookies:
            # Authenticate using api-key to get session cookie. This cannot
            # happen when the object is created, as requests may issue
            # pingbacks to different urls.
            url_parts = (url.scheme, url.netloc, API_KEY_LOGIN_PATH, '', '')
            data = {
                'username': self._config['user'],
                'api_key': self._config['api-key'],
            }
            res = requests.post(urlparse.urlunsplit(url_parts), data=data)
            if res.status_code != 201:
                raise BugzillaAuthException('API-Key authentication failed')
            self._cookies[host] = 'rbsessionid=%s' % res.cookies['rbsessionid']

        headers = super(BugzillaAuthApiKey, self).headers(pingback_url)
        headers['Cookie'] = self._cookies[host]
        return headers


def instantiate_authentication():
    """Return the appropriate BugzillaAuth object."""
    bugzilla_config = config.get('bugzilla')
    if 'api-key' in bugzilla_config:
        return BugzillaAuthApiKey(bugzilla_config)
    else:
        return BugzillaAuthPassword(bugzilla_config)


def update_review(bugzilla_auth, pingback_url, data):
    """Sends the 'data' to the 'pingback_url', handing auth and errors"""
    try:
        res = requests.post(pingback_url,
                            data=data,
                            headers=bugzilla_auth.headers(pingback_url),
                            auth=bugzilla_auth.http_auth())
        if res.status_code == 401:
            raise BugzillaAuthException('Login failure')
        return res.status_code, res.text
    except BugzillaAuthException as e:
        return None, 'Failed to connect authenticate with MozReview: %s' % e
    except requests.exceptions.ConnectionError as e:
        return None, 'Failed to connect to MozReview: %s' % e
    except requests.exceptions.RequestException as e:
        return None, 'Failed to update MozReview: %s' % e
