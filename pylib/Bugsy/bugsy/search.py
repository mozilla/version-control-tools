import requests
from bug import Bug


class Search(object):
    """
        This allows searching for bugs in Bugzilla
    """
    def __init__(self, bugzilla_url, token):
        """
            Initialises the search object

            :param bugzilla_url: This is the Bugzilla REST URL endpoint. Defaults to None
            :param token: Login token generated when instantiating a Bugsy() object with
                          a valid username and password
        """
        self.bugzilla_url = bugzilla_url
        self.token = token
        self.includefields = ['version', 'id', 'summary', 'status', 'op_sys',
                              'resolution', 'product', 'component', 'platform']
        self.keywrds = []
        self.assigned = []
        self.summs = []
        self.whitebord = []

    def include_fields(self, *args):
        r"""
            Include fields is the fields that you want to be returned when searching. These
            are in addition to the fields that are always included below.

            :param args: items passed in will be turned into a list
            :returns: :class:`Search`

            >>> bugzilla.search_for.include_fields("flags")

            The following fields are always included in search:
                'version', 'id', 'summary', 'status', 'op_sys',
                'resolution', 'product', 'component', 'platform'
        """
        for arg in args:
            self.includefields.append(arg)
        return self

    def keywords(self, *args):
        r"""
            When search() is called it will search for the keywords passed in here

            :param args: items passed in will be turned into a list
            :returns: :class:`Search`

            >>> bugzilla.search_for.keywords("checkin-needed")
        """
        self.keywrds = list(args)
        return self

    def assigned_to(self, *args):
        r"""
            When search() is called it will search for bugs assigned to these users

            :param args: items passed in will be turned into a list
            :returns: :class:`Search`

            >>> bugzilla.search_for.assigned_to("dburns@mozilla.com")
        """
        self.assigned = list(args)
        return self

    def summary(self, *args):
        r"""
            When search is called it will search for bugs with the words passed into the
            methods

            :param args: items passed in will be turned into a list
            :returns: :class:`Search`

            >>> bugzilla.search_for.summary("663399")
        """
        self.summs = list(args)
        return self

    def whiteboard(self, *args):
        r"""
            When search is called it will search for bugs with the words passed into the
            methods

            :param args: items passed in will be turned into a list
            :returns: :class:`Search`

            >>> bugzilla.search_for.whiteboard("affects")
        """
        self.whitebord = list(args)
        return self

    def search(self):
        r"""
            Call the Bugzilla endpoint that will do the search. It will take the information
            used in other methods on the Search object and build up the query string. If no
            bugs are found then an empty list is returned.

            >>> bugs = bugzilla.search_for\
            ...                .keywords("checkin-needed")\
            ...                .include_fields("flags")\
            ...                .search()
        """
        include_fields = ""
        for field in self.includefields:
            include_fields = include_fields + "include_fields=%s&" % field

        keywrds = ""
        for word in self.keywrds:
            keywrds = keywrds + "keywords=%s&" % word

        assigned = ""
        for assign in self.assigned:
            assigned = assigned + "assigned_to=%s&" % assign

        sumary = ""
        for sums in self.summs:
            sumary = sumary + "short_desc=%s&short_desc_type=allwordssubstr&" % sums

        whiteb = ""
        for white in self.whitebord:
            whiteb = whiteb + "whiteboard=%s&short_desc_type=allwordssubstr&" % white


        url = self.bugzilla_url +"/bug?" + include_fields + keywrds + assigned + sumary + whiteb
        if self.token:
            url = url + "token=%s" % self.token
        results = requests.get(url).json()
        return [Bug(self.bugzilla_url, self.token, **bug) for bug in results['bugs']]