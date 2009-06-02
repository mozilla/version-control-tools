import urllib2
import base64
from xml.etree.ElementTree import fromstring as xmlfromstring

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
    if self.name not in ('review', 'superreview', 'ui-review') and not self.name.startswith('approval'):
      bug.ui.warn("Unknown flag %s" % self.name)
    setter = node.attrib['setter']
    self.setter = setter[:setter.index('@')]
    self.status = node.attrib['status']

  @property
  def abbrev(self):
    if self.name == 'ui-review':
      return 'ui-r'
    elif self.name == 'superreview':
      return 'sr'
    else:
      return self.name[0]

  # Compare by flag name
  def __cmp__(self, other):
    flagorder = [ 'r', 'sr', 'ui-r', 'a']
    return cmp(flagorder.index(self.abbrev),flagorder.index(other.abbrev))

class Patch(Attachment):
  _name = None
  def __init__(self, bug, node):
    Attachment.__init__(self, bug, node)
    self.flags = list(sorted(Flag(bug, n) for n in node.findall('flag')))
    self.data = base64.b64decode(node.find('data').text)
    # Remove the timezone from the patch date
    self.date = node.find('date').text[:-4]

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
    fmt = self.bug.ui.config('qimportbz', 'patch_format', "bug-%(bugnum)s")

    patchname = fmt % self.metadata
    
    # The patch name might have some illegal characters so we need to scrub those
    replacements = {
      '_' : [' ', ':'],
      '' : ['"', "'", '<', '>', '*']
    }
    for replacement,items in replacements.items():
      for char in items:
        patchname = patchname.replace(char,replacement)
    return patchname

  @property
  def commit_message(self):
    fmt = self.bug.ui.config('qimportbz', 'msg_format',
                             'Bug %(bugnum)s - "%(title)s" [%(flags)s]')
    return fmt % self.metadata

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
        fs = setteridx.pop(f.setter,None)
        if fs:
          flagnames = [f.abbrev for f in fs]
          flags.append('%s=%s' % ('+'.join(flagnames), fs[0].setter))

      joinstr = self.bug.ui.config('qimportbz', 'joinstr', ' ')
      return joinstr.join(flags)
    else:
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
  def __init__(self, ui, base, num):
    self.ui = ui
    self.num = num
    url = "https://%s/show_bug.cgi?ctype=xml&id=%s" % (base, num)
    ui.status("Fetching %s..." % url)
    stream = urllib2.urlopen(url)
    data = stream.read()
    ui.status("done\n")

    ui.status("Parsing...")
    xml = xmlfromstring(data)
    bug = xml.find("bug")
    self.title = bug.find('short_desc').text
    self.attachments = [Attachment.parse(self, a) for a in xml.findall("bug/attachment")]
    self.comments = [Comment(n) for n in xml.findall("bug/long_desc")]
    ui.status("done\n")
    if bug.get("error") == "NotPermitted":
      ui.write("Not allowed to access bug.  (Perhaps it is marked with a security group?)")
      return

  @property
  def patches(self):
    return [attachment for attachment in self.attachments if isinstance(attachment,Patch)]
