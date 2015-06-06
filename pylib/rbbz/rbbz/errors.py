from reviewboard.reviews.errors import PublishError

#
# Review request errors.
#
class InvalidBugsError(PublishError):
    def __init__(self):
        PublishError.__init__(self, 'Exactly one bug ID must be provided.')


class InvalidBugIdError(PublishError):
    def __init__(self, bug_id):
        PublishError.__init__(self, 'Invalid bug ID "%s".' % bug_id)


class ConfidentialBugError(PublishError):
    def __init__(self):
        PublishError.__init__(self, 'This bug is confidential; please attach '
                              'the patch directly to the bug.')
