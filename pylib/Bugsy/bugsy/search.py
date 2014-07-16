import copy

import requests
from bug import Bug
import bugsy as Bugsy


class Search(object):
    """
        This allows searching for bugs in Bugzilla
    """
    def __init__(self, bugsy):
        """
            Initialises the search object

            :param bugsy: Bugsy instance to use to connect to Bugzilla.
        """
        self._bugsy = bugsy
        self._includefields = copy.copy(bugsy.DEFAULT_SEARCH)
        self._keywords = []
        self._assigned = []
        self._summaries = []
        self._whiteboard = []
        self._bug_numbers = []

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
            self._includefields.append(arg)
        return self

    def keywords(self, *args):
        r"""
            When search() is called it will search for the keywords passed in here

            :param args: items passed in will be turned into a list
            :returns: :class:`Search`

            >>> bugzilla.search_for.keywords("checkin-needed")
        """
        self._keywords = list(args)
        return self

    def assigned_to(self, *args):
        r"""
            When search() is called it will search for bugs assigned to these users

            :param args: items passed in will be turned into a list
            :returns: :class:`Search`

            >>> bugzilla.search_for.assigned_to("dburns@mozilla.com")
        """
        self._assigned = list(args)
        return self

    def summary(self, *args):
        r"""
            When search is called it will search for bugs with the words passed into the
            methods

            :param args: items passed in will be turned into a list
            :returns: :class:`Search`

            >>> bugzilla.search_for.summary("663399")
        """
        self._summaries = list(args)
        return self

    def whiteboard(self, *args):
        r"""
            When search is called it will search for bugs with the words passed into the
            methods

            :param args: items passed in will be turned into a list
            :returns: :class:`Search`

            >>> bugzilla.search_for.whiteboard("affects")
        """
        self._whiteboard = list(args)
        return self

    def bug_number(self, bug_numbers):
        r"""
            When you want to search for a bugs and be able to change the fields returned.

            :param bug_numbers: A string for the bug number or a list of strings
            :returns: :class:`Search`

            >>> bugzilla.search_for.bug_number(['123123', '123456'])
        """
        self._bug_numbers = list(bug_numbers)
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
        params = {}
        if self._includefields:
            params['include_fields'] = list(self._includefields)
        if self._bug_numbers:
            bugs = []
            for bug in self._bug_numbers:
                result = self._bugsy.request('bug/%s' % bug, params=params).json()
                bugs.append(Bug(self._bugsy, **result['bugs'][0]))

            return bugs
        else:
            if self._keywords:
                params['keywords'] = list(self._keywords)
            if self._assigned:
                params['assigned_to'] = list(self._assigned)
            if self._summaries:
                params['short_desc_type'] = 'allwordssubstr'
                params['short_desc'] = list(self._summaries)
            if self._whiteboard:
                params['short_desc_type'] = 'allwordssubstr'
                params['whiteboard'] = list(self._whiteboard)

            results = self._bugsy.request('bug', params=params).json()
            return [Bug(self._bugsy, **bug) for bug in results['bugs']]
