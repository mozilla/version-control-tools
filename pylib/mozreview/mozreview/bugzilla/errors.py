class BugzillaError(Exception):
    def __init__(self, msg, fault_code=None):
        super(BugzillaError, self).__init__(msg)
        self.msg = msg
        self.fault_code = fault_code


class BugzillaUrlError(BugzillaError):
    def __init__(self):
        BugzillaError.__init__(self, 'No Bugzilla URL provided in rbbz '
                               'configuration.')
