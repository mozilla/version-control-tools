from django.db import models


class FileDiffReviewer(models.Model):
    """N-N relationship between FileDiff and Reviewer

    This relationship allows to keep track of which files have been reviewed in
    a review.
    """
    # Unfortunately, Review Board extensions can't take advantage of the
    # ForeignKey ORM magic that Django provides. This is because the extension
    # loading mechanism doesn't do enough (yet) to flush out the foreign key
    # caches in Django.
    file_diff_id = models.IntegerField()
    reviewer_id = models.IntegerField()
    reviewed = models.BooleanField(default=False)
    last_modified = models.DateTimeField(auto_now_add=True)

    class Meta:
        app_label = 'mozreview'
        unique_together = ('file_diff_id', 'reviewer_id')
