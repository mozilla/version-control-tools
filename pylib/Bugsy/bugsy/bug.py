import datetime
import requests


VALID_STATUS = ["RESOLVED", "ASSIGNED", "NEW", "UNCONFIRMED"]
VALID_RESOLUTION = ["FIXED", "INCOMPLETE", "INVALID", "WORKSFORME", "DUPLICATE", "WONTFIX"]

def str2datetime(s):
    return datetime.datetime.strptime(s, '%Y-%m-%dT%H:%M:%SZ')

class BugException(Exception):
    """
        If we try do something that is not allowed to a bug then
        this error is raised
    """
    def __init__(self, msg):
        self.msg = msg

    def __str__(self):
        return "Message: %s" % self.msg


class Bug(object):
    """This represents a Bugzilla Bug"""

    def __init__(self, bugsy=None, **kwargs):
        """
            Defaults are set if there are no kwargs passed in. To pass in
            a dict create the Bug object like the following

            :param bugsy: Bugsy instance to use to connect to Bugzilla.

            >>> bug = Bug(**myDict)
        """
        self._bugsy = bugsy
        self._bug = dict(**kwargs)
        self._bug['op_sys'] = kwargs.get('op_sys', 'All')
        self._bug['product'] = kwargs.get('product', 'core')
        self._bug['component'] = kwargs.get('component', 'general')
        self._bug['platform'] = kwargs.get('platform', 'All')
        self._bug['version'] = kwargs.get('version', 'unspecified')

    @property
    def id(self):
        """
        Property for getting the ID of a bug.

        >>> bug.id
        123456
        """
        return self._bug.get('id', None)

    @property
    def summary(self):
        """
            Property for getting and setting the bug summary

            >>> bug.summary
            "I like cheese"
        """
        return self._bug.get('summary', '')

    @summary.setter
    def summary(self, value):
        """
            Property for getting and setting the bug summary

            >>> bug.summary = "I like cheese"
        """
        self._bug['summary'] = value

    @property
    def status(self):
        """
            Property for getting or setting the bug status

            >>> bug.status
            "REOPENED"
        """
        return self._bug.get('status', '')

    @status.setter
    def status(self, value):
        """
            Property for getting or setting the bug status

            >>> bug.status = "REOPENED"
        """
        if self._bug.get('id', None):
            if value in VALID_STATUS:
                self._bug['status'] = value
            else:
                raise BugException("Invalid status type was used")
        else:
            raise BugException("Can not set status unless there is a bug id. Please call Update() before setting")

    @property
    def OS(self):
        """
            Property for getting or setting the OS that the bug occured on

            >>> bug.OS
            "All"
        """
        return self._bug['op_sys']

    @OS.setter
    def OS(self, value):
        """
            Property for getting or setting the OS that the bug occured on

            >>> bug.OS = "Linux"
        """
        self._bug['op_sys']

    @property
    def resolution(self):
        """
            Property for getting or setting the bug resolution

            >>> bug.resolution
            "FIXED"
        """
        return self._bug['resolution']

    @resolution.setter
    def resolution(self, value):
        """
            Property for getting or setting the bug resolution

            >>> bug.resolution = "FIXED"
        """
        if value in VALID_RESOLUTION:
            self._bug['resolution'] = value
        else:
            raise BugException("Invalid resolution type was used")

    @property
    def product(self):
        """
            Property for getting the bug product

            >>> bug.product
            Core
        """
        return self._bug['product']

    @product.setter
    def product(self, value):
        """
            Property for getting the bug product

            >>> bug.product = "DOM"
        """
        self._bug['product'] = value

    @property
    def component(self):
        """
            Property for getting the bug component

            >>> bug.component
            General
        """
        return self._bug['component']

    @component.setter
    def component(self, value):
        """
            Property for getting the bug component

            >>> bug.component = "Marionette"
        """
        self._bug['component'] = value

    @property
    def platform(self):
        """
            Property for getting the bug platform

            >>> bug.platform
            "ARM"
        """
        return self._bug['platform']

    @platform.setter
    def platform(self, value):
        """
            Property for getting the bug platform

            >>> bug.platform = "OSX"
        """
        self._bug['platform'] = value

    @property
    def version(self):
        """
            Property for getting the bug platform

            >>> bug.version
            "TRUNK"
        """
        return self._bug['version']

    @version.setter
    def version(self, value):
        """
            Property for getting the bug platform

            >>> bug.version = "0.3"
        """
        self._bug['version'] = value

    def to_dict(self):
        """
            Return the raw dict that is used inside this object
        """
        return self._bug

    def update(self):
        """
            Update this object with the latest changes from Bugzilla

            >>> bug.status
            'NEW'
            #Changes happen on Bugzilla
            >>> bug.update()
            >>> bug.status
            'FIXED'
        """
        if self._bug.has_key('id'):
            result = self._bugsy.request('bug/%s' % self._bug['id']).json()
            self._bug = dict(**result['bugs'][0])
        else:
            raise BugException("Unable to update bug that isn't in Bugzilla")

    def get_comments(self):
        """
            Obtain comments for this bug.

            Returns a list of Comment instances.
        """
        bug = unicode(self._bug['id'])
        res = self._bugsy.request('bug/%s/comment' % bug).json()

        return [Comment(**comments) for comments in res['bugs'][bug]['comments']]

    def add_comment(self, comment):
        """
            Adds a comment to a bug. If a bug does not have a bug ID then you need
            call `put` on the :class:`Bugsy` class.

            >>> bug.add_comment("I like sausages")
            >>> bugzilla.put(bug)

            If it does have a bug id then this will do a post to the server

            >>> bug.add_comment("I like eggs too")
        """
        # If we have a key post immediately otherwise hold onto it until put(bug)
        # is called
        if self._bug.has_key('id'):
            self._bugsy.session.post('%s/bug/%s/comment' % (self._bugsy.bugzilla_url, self._bug['id']), data={"comment": comment}, )
        else:
            self._bug['comment'] = comment

    def to_dict(self):
        """
            Return the raw dict that is used inside this object
        """
        return self._bug


class Comment(object):
    """
        Represents a single Bugzilla comment.
    """

    def __init__(self, **kwargs):

        self.attachment_id = kwargs['attachment_id']
        self.author = kwargs['author']
        self.bug_id = kwargs['bug_id']
        self.creation_time = str2datetime(kwargs['creation_time'])
        self.creator = kwargs['creator']
        self.id = kwargs['id']
        self.is_private = kwargs['is_private']
        self.text = kwargs['text']
        self.time = str2datetime(kwargs['time'])

        if 'tags' in kwargs:
            self.tags = set(kwargs['tags'])

