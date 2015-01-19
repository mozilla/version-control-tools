from reviewboard.extensions.base import Extension


class MozReviewExtension(Extension):
    metadata = {
        'Name': 'mozreview',
        'Summary': 'MozReview extension to Review Board',
    }

    def initialize(self):
        pass
