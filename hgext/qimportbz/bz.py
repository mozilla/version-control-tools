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
    self.filename = node.find('filename').text

  def parse(bug, node):
    ctor = Attachment
    if node.attrib['ispatch'] == "1":
      ctor = Patch
    return ctor(bug, node)

  parse = staticmethod(parse)

class Flag(object):
  def __init__(self, bug, node):
    def removeDomain(emailAddress):
      """Removes domain from email address if (old) Bugzilla didn't do it."""
      # Bugzilla v3.2.1+: "Email Addresses Hidden From Logged-Out Users For Oracle Users"
      # Bugzilla v3.4.1+: "Email Addresses Hidden From Logged-Out Users"
      at_idx = emailAddress.find('@')
      return emailAddress if at_idx < 0 else emailAddress[:at_idx]

    # Ignored node attributes: 'id' and 'type_id'.

    self.name = node.attrib['name']
    if self.name not in ('review', 'superreview', 'ui-review', 'checked-in') and not self.name.startswith('approval'):
      bug.settings.ui.warn("Unknown flag %s\n" % self.name)

    self.setter = removeDomain(node.attrib['setter'])

    self.status = node.attrib['status']

    self.requestee = removeDomain(node.attrib['requestee']) if 'requestee' in node.attrib else None

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

    # Remove seconds (which are always ':00') and timezone from the patch date:
    # keep 'yyyy-mm-dd hh:mn' only.
    self.date = date or node.find('date').text[:16]

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
      "flags" : self.joinFlags(),
      "filename" : self.filename,
    }

  @property
  def name(self):
    if self.bug.settings.patch_format:
      # Create new patch name.
      patchname = self.bug.settings.patch_format % self.metadata
    else:
      # Use filename from bug attachment.
      patchname = self.filename

    # The patch name might have some illegal characters so we need to scrub those
    replacements = {
      '_' : [' ', ':'],
      '' : ['"', "'", '<', '>', '*']
    }
    for replacement, items in replacements.items():
      for char in items:
        patchname = patchname.replace(char, replacement)

    return patchname

  def joinFlags(self, commitfmt=True):
    """Join any flags together that have the same setter, returning a string in sorted order.
    If commitfmt is False, simply list all flags.
    """
    if not commitfmt:
      return ', '.join('%s: %s%s%s' % (f.setter, f.name, f.status, " (%s)" % f.requestee if f.requestee else "") for f in self.flags)

    flags = []
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

class Comment(object):
  def __init__(self, node):
    who = node.find('who')
    self.who = who.attrib['name']
    self.who_email = who.text

    # Remove seconds and timezone from the post date:
    # keep 'yyyy-mm-dd hh:mn' only.
    self.date = node.find('bug_when').text[:16]

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
