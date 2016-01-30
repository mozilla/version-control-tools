from __future__ import unicode_literals

from djblets.util.decorators import (
    simple_decorator,
)
from reviewboard.reviews.errors import (
    PublishError,
)


class BugzillaError(Exception):
    def __init__(self, msg, fault_code=None):
        super(BugzillaError, self).__init__(msg)
        self.msg = msg
        self.fault_code = fault_code


class BugzillaUrlError(BugzillaError):
    def __init__(self):
        BugzillaError.__init__(self, 'No Bugzilla URL provided in rbbz '
                               'configuration.')


@simple_decorator
def bugzilla_to_publish_errors(func):
    def _transform_errors(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except BugzillaError as e:
            raise PublishError('Bugzilla error: %s' % e.msg)
    return _transform_errors
