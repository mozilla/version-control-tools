from reviewboard.reviews.errors import PublishError

class InvalidBugIdError(PublishError):
    def __init__(self):
        PublishError.__init__(self, 'invalid bug ID')


class BugNotFoundError(PublishError):
    def __init__(self, bug_id):
        PublishError.__init__(self, 'bug %d not found' % bug_id)


class NoBugError(PublishError):
    def __init__(self):
        PublishError.__init__(self, 'no bug ID provided')


class InvalidReviewerError(PublishError):
    def __init__(self):
        PublishError.__init__(self, 'invalid reviewer')


class BugzillaError(Exception):
    def __init__(self, msg):
        self.msg = msg


class BugzillaAuthError(BugzillaError):
    pass


class BugzillaUrlError(BugzillaError):
    pass
