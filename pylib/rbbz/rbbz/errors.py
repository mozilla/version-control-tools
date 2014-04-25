from reviewboard.reviews.errors import PublishError

class BugNotFoundError(PublishError):
    def __init__(self, bug_id):
        PublishError.__init__(self, 'bug %d not found' % bug_id)


class BugzillaError(Exception):
    pass


class BugzillaAuthError(BugzillaError):
    pass
