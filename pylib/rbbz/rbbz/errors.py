from reviewboard.reviews.errors import PublishError

#
# Review request errors.
#
class InvalidBugsError(PublishError):
    def __init__(self):
        PublishError.__init__(self, 'Exactly one bug ID must be provided.')
