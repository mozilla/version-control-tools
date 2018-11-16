# This software may be used and distributed according to the terms of the
# GNU General Public License version 2 or any later version.

'''S3 content redirect caching for wire protocol v2

This plugin implements an S3 cacher for CBOR encoded objects
in the Mercurial wire protocol v2. Server operators can provide AWS
credentials and the name of a bucket which will act as the cache.
The cacher will take a key and send an HTTP HEAD request to AWS,
which will throw a 404 error if the object does not exist (ie
a cache miss). In the event the object exists in S3, a presigned
url is generated and a content redirect response is issued to
the client.

::

    [extensions]
    wireprotocache =
    [wireprotocache]
    plugin = s3
    [wireprotocache.s3]
    # configure auth
    access-key-id = accesskeyid
    secret-access-key = secretaccesskey
    # set the bucket to cache objects in
    bucket = cachebucket
    # specify S3 domains as redirect targets
    redirecttargets = https://s3-us-west-2.amazonaws.com/,\
                      https://s3-us-east-2.amazonaws.com/

    # specify region (optional, will query AWS if empty)
    region = us-east-2

    # set minimum object size in bytes (optional)
    minimumobjectsize = 500

    # set object ACL in S3 (optional, default public-read)
    cacheacl = private

    # specify alternative endpoint url (optional, testing)
    endpoint_url = http://localhost:12345/
'''

from __future__ import absolute_import

from mercurial import (
    repository,
    wireprototypes,
)
from mercurial.utils import (
    interfaceutil,
)

import boto3
import botocore.exceptions


def create_redirect_url(client, bucket, key):
    '''Returns a bytes redirect url for the object `key` in
    `bucket`.
    '''
    params = {
        'Bucket': bucket,
        'Key': key,
    }
    url = client.generate_presigned_url('get_object',
                                        Params=params)

    return bytes(url)


def put_s3(client, bucket, key, cacheobject, cacheacl):
    '''Puts the `object` into the S3 `bucket` as `key`.
    '''
    params = {
        'ACL': cacheacl,
        'Body': cacheobject,
        'Bucket': bucket,
        'ContentType': b'application/mercurial-cbor',
        'Key': key,
    }

    client.put_object(**params)


def is_s3cache_hit(client, bucket, key):
    '''Returns `True` if the key is present in the S3 cache
    bucket.
    '''
    try:
        params = {
            'Bucket': bucket,
            'Key': key,
        }

        # If this doesn't throw, the object exists
        client.head_object(**params)
        return True

    except botocore.exceptions.ClientError as e:
        # 404 indicated the object does not exist
        if e.response['Error']['Code'] == '404':
            return False

        # Throw other boto3 errors for logging
        # by caller
        raise


@interfaceutil.implementer(repository.iwireprotocolcommandcacher)
class s3wireprotocache(object):
    def __init__(self, ui, command, encodefn, redirecttargets, redirecthashes,
                 req):
        self.ui = ui
        self.encodefn = encodefn

        self.redirecttargets = redirecttargets
        self.redirecthashes = redirecthashes

        self.req = req
        self.key = None

        # Auth config
        self.access_key_id = ui.config('wireprotocache.s3',
                                       'access-key-id')
        self.secret_access_key = ui.config('wireprotocache.s3',
                                           'secret-access-key')
        self.s3_endpoint_url = ui.config('wireprotocache.s3',
                                         'endpoint_url')

        clientparams = {
            'aws_access_key_id': self.access_key_id,
            'aws_secret_access_key': self.secret_access_key,
        }

        # Alternative endpoint for testing
        if self.s3_endpoint_url:
            clientparams['endpoint_url'] = self.s3_endpoint_url

        # TODO consider holding a client reference in a global variable
        self.s3 = boto3.client('s3', **clientparams)

        # Bucket name and region
        self.bucket = ui.config('wireprotocache.s3', 'bucket')
        self.region = ui.config('wireprotocache.s3', 'region')

        self.cacheacl = ui.config('wireprotocache.s3', 'cacheacl')

        self.minimumobjectsize = ui.configint('wireprotocache.s3',
                                              'minimumobjectsize')

        # Append objects here to be cached during `onfinished`
        self.buffered = []

        # Indicates if the result was a cache hit or miss
        self.cachehit = False

        # Scrub 'repo' key from cache key state (useful for testing)
        self.delete_repo_keystate = ui.configbool('wireprotocache.s3',
                                                  'delete-repo-keystate')

        ui.log('wireprotocache', 's3 cacher constructed for %s\n', command)

    def __enter__(self):
        return self

    def __exit__(self, exctype, excvalue, exctb):
        if exctype:
            self.ui.log('wireprotocache', 'cacher exiting due to error\n')

    def adjustcachekeystate(self, state):
        if self.delete_repo_keystate:  # testing backdoor
            del state[b'repo']
        return

    def setcachekey(self, key):
        '''Set the cache key for future lookup
        '''
        # TODO consider partitioning keys by command
        self.key = key
        return True

    def lookup(self):
        '''Lookup the previously set key within the cache
        '''
        try:
            self.cachehit = is_s3cache_hit(self.s3, self.bucket, self.key)

            if self.cachehit:
                self.ui.log('wireprotocache', '%s: cache hit, creating redirect response\n' % self.key)

                url = create_redirect_url(self.s3, self.bucket, self.key)

                self.ui.log('wireprotocache',
                            '%s: serving redirect response to %s\n', self.key, url)

                response = wireprototypes.alternatelocationresponse(
                    mediatype=b'application/mercurial-cbor',
                    url=url,
                )

                # TODO: preserve compression from the response as followup

                return {'objs': [response]}
            else:
                self.ui.log('wireprotocache', '%s: cache miss\n', self.key)

        except botocore.exceptions.ClientError as e:
            self.ui.log('wireprotocache', '%s: boto3 errored out: %s\n',
                        self.key, e)

        return None

    def onobject(self, obj):
        '''Buffers the object to be inserted into the cache,
        if the key was not a cache hit
        '''
        # TODO stream objects via multipart upload or otherwise to avoid excessive buffering
        if not self.cachehit:
            self.buffered.extend(self.encodefn(obj))
        yield obj

    def onfinished(self):
        '''Inserts buffered objects into the cache
        '''
        if not self.buffered:
            return []

        # Check the size of the object and assert it reaches minimum object size
        entry = b''.join(self.buffered)
        if len(entry) < self.minimumobjectsize:
            self.ui.log('wireprotocache',
                        'obj size (%s) is below minimum of %s; not caching\n'
                        % (len(entry), self.minimumobjectsize))
            return []

        self.ui.log('wireprotocache', '%s: storing cache entry\n'
                    % self.key)
        put_s3(self.s3, self.bucket, self.key, entry, self.cacheacl)

        return []


def parse_lowest_level_domain(redirect):
    '''Grabs the lowest level domain from
    a redirect target.
    '''
    return redirect.replace(b'https://', b'').split(b'.')[0]


def getadvertisedredirecttargets(orig, repo, proto):
    '''Converts list of comma separated redirect targets
    urls to the advertised redirect target format
    '''
    ui = repo.ui

    redirectconf = ui.config('wireprotocache.s3', 'redirecttargets')
    redirects = redirectconf.split(b',')

    redirects = [
        {
            'name': parse_lowest_level_domain(r),
            'protocol': b'https',
            'snirequired': True,
            'tlsversions': [b'1.1', b'1.2'],
            'uris': r,
        }
        for r in redirects
    ]

    return redirects


def makeresponsecacher(orig, repo, proto, command, args, objencoderfn,
                       redirecttargets, redirecthashes):
    '''Monkey-patch function to provide custom response cacher
    '''
    return s3wireprotocache(repo.ui, command, objencoderfn,
                            redirecttargets, redirecthashes, proto._req)
