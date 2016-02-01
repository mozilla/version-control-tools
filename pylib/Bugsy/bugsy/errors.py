class BugsyException(Exception):
    """
        If while interacting with Bugzilla and we try do something that is not
        supported this error will be raised.
    """
    def __init__(self, msg, error_code=None):
        self.msg = msg
        self.code = error_code

    def __str__(self):
        return "Message: {message} Code: {code}".format(message=self.msg,
                                                        code=self.code)


class LoginException(BugsyException):
    """
        If a username and password are passed in but we don't receive a token
        then this error will be raised.
    """
    pass


class BugException(BugsyException):
    """
        If we try do something that is not allowed to a bug then
        this error is raised
    """
    pass


class SearchException(BugsyException):
    """
        If while interacting with Bugzilla and we try do something that is not
        supported this error will be raised.
    """
    pass
