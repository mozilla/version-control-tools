import config
import logging
import requests
import urlparse


logger = logging.getLogger('autoland')


class LandoPingback(object):
    """Handle updating Lando requests."""

    def __init__(self):
        self.name = 'lando'
        self.auth = {}

    def update(self, pingback_url, data):
        """Sends the 'data' to the 'pingback_url', handing auth and errors"""

        try:
            # Grab the api-key for this hostname.
            hostname = urlparse.urlparse(pingback_url).hostname
            if hostname not in self.auth:
                auth_config = config.get('pingback').get(hostname)
                self.auth[hostname] = auth_config['api-key']

            res = requests.post(pingback_url,
                                data=data,
                                headers={'API-Key': self.auth[hostname]})

            if res.status_code != 200:
                return None, res.text
            return res.status_code, res.text
        except requests.exceptions.ConnectionError as e:
            return None, 'Failed to connect to Lando: %s' % e
        except requests.exceptions.RequestException as e:
            return None, 'Failed to update Lando: %s' % e
