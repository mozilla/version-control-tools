class BugNotFoundError(Exception):
    def __init__(self, bug_id):
        self.bug_id = bug_id

    def __str__(self):
        return 'bug %d not found' % self.bug_id
