class Push(object):
    """This represents a Push"""

    def __init__(self, push_id, push_info=None):
        """
        We set Push object default as dict, and we will
        give each push a push id when we init it.

        :param push_id:    The push id of this push.
        :type  push_id:    str
        :param push_info:  Metadata about the push. For example:
             {u'date': 1476374097,
             u'changesets': [u'67ff6167e020cca50fa2a64c16c1e1074b8a2871'],
             u'user': u'armenzg@mozilla.com'}

             {u'date': 1441983569,
             u'changesets': [{
                 u'files': [u'main.cpp'],
                 u'node': u'2dc063b51c0eea1b6b026253a2d8d3421716b197',
                 u'tags': [u'test_tags'],
                 u'author': u'Chris Peterson <cpeterson@mozilla.com>',
                 u'branch': u'default',
                 u'desc': u'try: -b do -p win32,win32-mulet,win64,win32_gecko '
                           '-u all[Windows XP,Windows 7,Windows 8,b2g] -t none'
             }],
             u'user': u'nobody@mozilla.com'}
        :type  push_info:  dict
        """
        self._id = push_id
        if push_info:
            self._push = dict()
            self._push['changesets'] = []
            self._push['date'] = push_info.get('date', None)
            self._push['user'] = push_info.get('user', None)
            for changeset in push_info.get('changesets'):
                # When we query push date without 'full=1' option, the changeset
                # we get will be a list of strings rather than an object.
                if isinstance(changeset, basestring):
                    assert len(changeset) == 40, \
                        'All changesets have to be of 40 chars in length.'
                    self._push['changesets'].append(Changeset(node=changeset))
                else:
                    assert len(changeset['node']) == 40, \
                        'All changesets have to be of 40 chars in length.'
                    self._push['changesets'].append(Changeset(**changeset))

    def __repr__(self):
        return "<Push id:%s info:%s>" % (self._id, self._push)

    def __cmp__(self, other):
        return cmp(self.id, other.id)

    @property
    def id(self):
        """
            Property for getting the Push ID of a push.
            >>> push.id
            123456
        """
        return self._id

    @property
    def changesets(self):
        """
            Property for getting a list of changeset objects of a push.
            >>> push.changesets
            >>> [changeset1, changeset2]
        """
        return self._push.get('changesets', None)

    @property
    def date(self):
        """
            Property for getting the UNIX timestamp of a push.
            >>> push.date
            >>> 1423829062
        """
        return self._push.get('date', None)

    @property
    def user(self):
        """
            Property for getting the information for
            the user who commited this push.
            >>> push.user
            >>> nobody@gmail.com
        """
        return self._push.get('user', None)


class Changeset(object):
    """This represents a Changeset"""
    def __init__(self, **kwargs):
        self._changeset = dict(**kwargs)

    def __repr__(self):
        return "<changeset %s>" % self._changeset

    def __cmp__(self, other):
        return cmp(self.node, other.node)

    @property
    def author(self):
        """
            Property for getting the author of this changeset.
            >>> Changeset.author
            nonbody@gmail.com
        """
        return self._changeset.get('author', None)

    @property
    def branch(self):
        """
            Property for getting the branch name of this changeset.
            >>> Changeset.branch
            >>> 'default'
        """
        return self._changeset.get('branch', None)

    @property
    def desc(self):
        """
            Property to represent where this changeset comes from
            >>> Changeset.desc
            >>> "Bug 1234455. demoe bug for this priperty"
        """
        return self._changeset.get('desc', None)

    @property
    def files(self):
        """
            a list which shows those files been addressed in this changeset.
            >>> Changeset.files
            >>> ["widget/windows/WinUtils.cpp", "widget/windows/WinUtils.h"]
        """
        return self._changeset.get('files', [])

    @property
    def node(self):
        """
            Property for getting the node ID(revision) of a changeset.
            >>> Changeset.node
            123456
        """
        return self._changeset.get('node', [])

    @property
    def tags(self):
        """
            Property for getting the tags for a changeset.
            >>> Changeset.tags
            >>> ['tag_name']
        """
        return self._changeset.get('tags', None)
