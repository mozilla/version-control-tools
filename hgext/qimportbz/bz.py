import os
import urllib2
import base64
from xml.etree.ElementTree import fromstring as xmlfromstring
try:
  import cStringIO as StringIO
except ImportError:
  import StringIO
import re

from mercurial import patch

# int(bug num) -> Bug
cache = {}

class Settings(object):
  def __init__(self, ui):
    self.ui = ui
    self.msg_format = ui.config('qimportbz', 'msg_format',
                                'Bug %(bugnum)s - "%(title)s" [%(flags)s]')
    self.joinstr = ui.config('qimportbz', 'joinstr', ' ')
    self.patch_format = ui.config('qimportbz', 'patch_format', "bug-%(bugnum)s")

class Attachment(object):
  def __init__(self, bug, node):
    self.bug = bug
    self.obsolete = node.attrib['isobsolete'] == "1"
    self.id = node.find('attachid').text
    self.desc = node.find('desc').text

  def parse(bug, node):
    ctor = Attachment
    if node.attrib['ispatch'] == "1":
      ctor = Patch
    return ctor(bug, node)

  parse = staticmethod(parse)

class Flag(object):
  def __init__(self, bug, node):
    self.name = node.attrib['name']
    if self.name not in ('review', 'superreview', 'ui-review', 'checked-in') and not self.name.startswith('approval'):
      bug.settings.ui.warn("Unknown flag %s\n" % self.name)

    setter = node.attrib['setter']
    setter_idx = setter.find('@')
    self.setter = setter if setter_idx < 0 else setter[:setter_idx]

    self.status = node.attrib['status']

  @property
  def abbrev(self):
    if self.name == 'ui-review':
      return 'ui-r'

    if self.name == 'superreview':
      return 'sr'

    return self.name[0]

  # Compare by flag name
  def __cmp__(self, other):
    flagorder = ['r', 'sr', 'ui-r', 'a', 'c']
    return cmp(flagorder.index(self.abbrev), flagorder.index(other.abbrev))

class Patch(Attachment):
  _name = None

  def __init__(self, bug, node):
    Attachment.__init__(self, bug, node)
    self.flags = list(sorted(Flag(bug, n) for n in node.findall('flag')))
    rawtext = base64.b64decode(node.find('data').text)
    data = StringIO.StringIO(rawtext)
    filename, message, user, date, branch, nodeid, p1, p2 = patch.extract(bug.settings.ui, data)
    # for some reason, patch.extract writes a temporary file with the diff hunks
    if filename:
      fp = file(filename)
      self.data = fp.read().decode('utf-8')
      fp.close()
      os.remove(filename)
    else:
      self.data = ''

    # Remove the timezone from the patch date
    self.date = date or node.find('date').text[:-4]

    if user:
      self.author = user
    else:
      for post in reversed(self.bug.comments):
        if post.date == self.date:
          self.author = "%s <%s>" % (
            # scrub the :cruft from the username
            re.sub("\(.*\)", "", re.sub("\[:\w+\]|\(:\w+\)|:\w+", "", post.who)).strip(),
            post.who_email)
          break
    self.commit_message = message.strip() or \
                          (self.bug.settings.msg_format % self.metadata)

  def __unicode__(self):
    return u"""
# vim: se ft=diff :
# User %s
# Date %s
%s

%s
""" % (self.author, self.date, self.commit_message, self.data)

  @property
  def metadata(self):
    return {
      "bugnum" : self.bug.num,
      "id" : self.id,
      "title" : self.bug.title,
      "desc" : self.desc,
      "flags" : self.joinFlags(True)
    }

  @property
  def name(self):
    patchname = self.bug.settings.patch_format % self.metadata

    # The patch name might have some illegal characters so we need to scrub those
    replacements = {
      '_' : [' ', ':'],
      '' : ['"', "'", '<', '>', '*']
    }
    for replacement, items in replacements.items():
      for char in items:
        patchname = patchname.replace(char, replacement)
    return patchname

  def joinFlags(self, commitfmt=False):
    """Join any flags together that have the same setter, returning a string in sorted order"""
    flags = []
    if commitfmt:
      setteridx = {}

      for f in self.flags:
        setter = f.setter
        if setter in setteridx:
          setteridx[setter].append(f)
        else:
          setteridx[setter] = [f]

      for f in self.flags:
        fs = setteridx.pop(f.setter, None)
        if fs:
          flagnames = [f.abbrev for f in fs]
          flags.append('%s=%s' % ('+'.join(flagnames), fs[0].setter))

      return self.bug.settings.joinstr.join(flags)

    return ', '.join('%s: %s%s' % (f.setter, f.name, f.status) for f in self.flags)

  @property
  def attacher(self):
    attacher_name = ''
    attacher_email = ''
    for post in reversed(self.bug.comments):
      if post.date == self.date:
        return post

class Comment(object):
  def __init__(self, node):
    who = node.find('who')
    self.who = who.attrib['name']
    self.who_email = who.text
    # remove the timezone and seconds from the post date
    self.date = node.find('bug_when').text[:-7]
    self.text = node.find('thetext').text

class Bug(object):
  def __init__(self, ui, data):
    self.settings = Settings(ui)
    xml = xmlfromstring(data)
    bug = xml.find("bug")
    self.num = int(bug.find('bug_id').text)
    self.title = bug.find('short_desc').text
    self.comments = [Comment(n) for n in xml.findall("bug/long_desc")]
    self.attachments = [Attachment.parse(self, a) for a in xml.findall("bug/attachment")]
    if bug.get("error") == "NotPermitted":
      raise PermissionError("Not allowed to access bug.  (Perhaps it is marked with a security group?)")

    # Add to cache so we can avoid network lookup later in this process
    cache[self.num] = self

  def get_patch(self, attachid):
    for attachment in self.attachments:
      if attachment.id == attachid:
        return attachment

    return None

  @property
  def patches(self):
    return [attachment for attachment in self.attachments if isinstance(attachment, Patch)]

class PermissionError(Exception):
  def __init__(self, msg):
    self.msg = msg

  def __str__(self):
    return self.msg
