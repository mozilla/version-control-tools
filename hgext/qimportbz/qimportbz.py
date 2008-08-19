#!/usr/local/bin/python
# Imports patches from bugzilla into the hg repo in the current working directory
import sys, os
import urllib2
import base64
from xml.etree.ElementTree import fromstring as xmlfromstring
from subprocess import Popen, PIPE
from optparse import OptionParser, make_option
import re
import pdb

def isGoodAttachment(a):
  if "0" == a.attrib['ispatch']: return False
  id = a.find('attachid').text
  desc = a.find('desc').text
  if options.verbose:
    print "Found patch %s (%s)" % (id, desc)
  isobsolete = int(a.attrib['isobsolete'])
  if isobsolete:
    if options.verbose:
      print "...but it was obsolete"
    return False
  return True

def cleanPatchName(patchname):
  replacements = {
    '_' : [' ', ':'],
    '' : ['"', "'", '<', '>', '*']
  }
  for replacement,items in replacements.items():
    for char in items:
      patchname = patchname.replace(char,replacement)
  return patchname

def cleanUserName(username):
  return re.sub("\(.*\)","", re.sub("\[:\w+\]|\(:\w+\)","",username)).strip()

def parsePatch(data):
  user = ''
  date = ''
  msg = []
  subject = ''
  # Based on mq.py
  format = None
  diffstart = 0
  lines = data.splitlines()
  for i,line in enumerate(lines):
    line = line.rstrip()
    if line.startswith('diff ') or line.startswith('--- ') or \
       line.startswith('+++ ') or line.startswith("Index: "):
      diffstart = i
      break
    if line == '# HG changeset patch':
      format = 'hgpatch'
    elif format == 'hgpatch':
      if line.startswith("# User "):
        user = line[7:]
      elif line.startswith("# Date "):
        date = line[7:]
      elif not line.startswith("# ") and line:
        msg.append(line)
        format = None
    elif format != "tagdone" and line.lower().startswith("subject: "):
      subject = line[9:]
      format = "tag"
    elif format != "tagdone" and line.lower().startswith("from: "):
      user = line[6:]
      format = "tag"
    elif format == "tag" and line == "":
      format = "tagdone"
    elif msg or line:
      msg.append(line)

  if format and format.startswith("tag") and subject:
    message.insert(0, '')
    message.insert(0, subject)

  diff = '\n'.join(lines[diffstart:])+'\n'
  return ('\n'.join(msg), user, date, diff)

def findAttacher(p):
  bug = p.attrib['bug']
  # Remove the timezone from the patch date
  patchdate = p.find('date').text[:-4]
  attacher_name = ''
  attacher_email = ''
  for post in reversed(bug.findall('bug/long_desc')):
    # remove the timezone and seconds from the post date
    postdate = post.find('bug_when').text[:-7]
    if postdate == patchdate:
      who = post.find('who')
      attacher_name = who.attrib['name']
      attacher_email = who.text
      break
  return attacher_name, attacher_email

def generateCommitMessageDefault(p):
  bug = p.attrib['bug']
  if options.desc:
    desc = options.desc
  else:
    descbits = []
    if options.attachdesc:
      descbits.append(p.find('desc').text)
    if options.bugtitle or not descbits:
      descbits.append(p.attrib['bug'].find('bug/short_desc').text)
    desc = ' '.join(descbits)
  flags = getFlagDesc(p, True)
  bugnum = bug.find('bug/bug_id').text
  return "%s - bug %s %s" % (desc, bugnum, flags)

def generateCommitMessageReed(p):
  bug = p.attrib['bug']
  bugnum = bug.find('bug/bug_id').text
  title = p.attrib['bug'].find('bug/short_desc').text
  attachdesc = p.find('desc').text
  flags = getFlagDesc(p, True)
  if options.attachdesc:
    return 'Bug %s - "%s" (%s) [%s]' % (bugnum, title, attachdesc, flags)
  else:
    return 'Bug %s - "%s" [%s]' % (bugnum, title, flags)

commit_formats = {
  'default' : generateCommitMessageDefault,
  'reed' : generateCommitMessageReed,
}

def generateCommitMessage(p):
  return commit_formats.get(options.commitfmt,generateCommitMessageDefault)(p)

def importPatch(p, patchname):
  bug = p.attrib['bug']
  patchname = cleanPatchName(patchname)
  data64 = p.find('data').text
  data = base64.b64decode(data64)
  msg, user, date, diff = parsePatch(data)
  if not msg:
    if options.message:
      msg = options.message
    else:
      msg = generateCommitMessage(p)
  if not user:
    username, useremail = findAttacher(p)
    if username and useremail:
      user = "%s <%s>" % (cleanUserName(username), useremail)
  # strip the date
  date = ''

  dataparts = []
  if user:
    dataparts.append('From: %s' % user)
  elif options.verbose:
    print "Warning: no user!"
  if msg:
    dataparts.append(msg)
  else:
    print "Warning: no commit message!"
  dataparts.append(diff)
  data = '\n\n'.join(dataparts)
  print msg
  args = ["hg", "qimport", "-n", patchname, "-"]
  if options.verbose:
    print "Running %s" % ' '.join(args)
  if options.readonly: return
  hg = Popen(args, stdin=PIPE)
  hg.stdin.write(data)
  hg.stdin.close()
  hg.wait()
  if hg.returncode:
    sys.exit(-2)

def getFlagDesc(p,commitfmt=False):
  descs = []
  def isKnownFlag(f):
    name = f.attrib['name']
    if name in ('review','superreview') or name.startswith('approval'):
      return f.attrib['status'] == '+' if commitfmt else True
    elif options.verbose:
      print "Unhandled flag %s" % name
    return False
  def flagAbbrev(f):
    name = f.attrib['name']
    return 'sr' if name == 'superreview' else name[0]
  def getSetter(f):
    setter = f.attrib['setter']
    return setter[:setter.index('@')]
  flagdata = [{ 'abbrev' : flagAbbrev(f),
                'name' : f.attrib['name'],
                'status' : f.attrib['status'],
                'setter' : getSetter(f)
              } for f in p.findall('flag') if isKnownFlag(f)]
  if commitfmt:
    setteridx = {}
    for f in flagdata:
      setter = f['setter']
      if setter in setteridx:
        setteridx[setter].append(f)
      else:
        setteridx[setter] = [f]
    for f in flagdata:
      fs = setteridx.pop(f['setter'],None)
      if fs:
        flagnames = [f['abbrev'] for f in fs]
        descs.append('%s=%s' % ('+'.join(flagnames), fs[0]['setter']))
    return ' '.join(descs)
  else:
    for f in flagdata:
      descs.append('%s: %s%s' % (f['setter'], f['name'], f['status']))
    return ', '.join(descs)

def cleanChoice(c):
  return int(c.strip())

def multiplePatchChoose(patches):
  for i,p in enumerate(patches):
    desc = p.find('desc').text
    flags = getFlagDesc(p)
    print "%s: %s %s" % (i+1, desc, flags)
  choicestr = raw_input("Which patches do you want to import? ")
  return [cleanChoice(s)-1 for t in choicestr.split(',') for s in t.split()]

class BaseCommand(object):
  options = []
  defaults = {}
  usage = ""

class Help(BaseCommand):
  usage = "%prog command [options]"
  def run(self):
    parser.print_help()

class Import(BaseCommand):
  options = [
    make_option("-t", "--bug-title", action="store_true", dest="bugtitle", help="Use the bug title to generate a commit message"),
    make_option("-a", "--attachment-desc", action="store_true", dest="attachdesc", help="Use the attachment's description to generate a commit message"),
    make_option("-m", "--message", dest="message", help="Commit message"),
    make_option("-d", "--description", dest="desc", help="Patch description"),
    make_option("-n", "--patch-name", dest="patchname", help="Patch name"),
    make_option("-u", "--use-attach-desc", action="store_true", dest="useattachdesc", help="Use the attachment description in the patch name"),
    make_option("-f", "--format", dest="commitfmt", help="Specify commit format. Possible values are: %s" % ', '.join(commit_formats.keys())),
    make_option("--reed", action="store_const", dest="commitfmt", const="reed", help="Use reed's commit format")
  ]
  defaults = {
    "bugtitle" : True,
    "attachdesc" : False,
    "message" : '',
    "desc" : '',
    "patchname" : '',
    "useattachdesc" : False,
    "commitfm" : "default"
  }
  usage = "%prog import [options] bugnumber [bugnumber...]"
  def do_bug(self, bugnum):
    url = "https://%s/show_bug.cgi?ctype=xml&id=%s" % (options.bugzilla, bugnum)
    if options.verbose:
      print ("Fetching from %s..." % url),
    stream = urllib2.urlopen(url)
    data = stream.read()
    if options.verbose:
      print "\bdone"
    #print "Got %s bytes of data" % len(data)
    if options.verbose:
      print "Parsing bug...",
    xml = xmlfromstring(data)
    if options.verbose:
      print "\bdone"
    attachments = xml.findall("bug/attachment")
    patches = [a for a in attachments if isGoodAttachment(a)]
    for patch in patches:
      patch.attrib['bug'] = xml

    def getPatchName(p):
      if options.patchname:
        return options.patchname
      if options.useattachdesc:
        desc = p.find('desc').text
        return "bug%s_%s" % (bugnum, desc)
      else:
        return "bug%s" % bugnum

    if len(patches) == 1:
      patch = patches[0]
      importPatch(patch, getPatchName(patch))
    elif len(patches) > 1:
      if options.verbose:
        print "Found multiple patches"
      choices = multiplePatchChoose(patches)
      #choicestr = raw_input("Import as separate patches (y/n)? ")
      #separatePatches = 'y' in choicestr.lower()
      for choice in choices:
        patch = patches[choice]
        importPatch(patch, getPatchName(patch))
    # patcheswithreview = [patch for patch in patches
    #                            if len(
    #                               [f for f in patch.findall('flag')
    #                                  if f.attrib['name'] == 'review' and f.attrib['status'] == '+'
    #                               ])]
    # if len(patcheswithreview) == 1:
    #   print "Found one patch"
    #   importPatch(patcheswithreview[0])
    #   exit(-1)
    # elif len(patcheswithreview) > 1:
    #   print "Found multiple patches with r+"
    # else:
    #   print "Found no patches with review"
    else:
      if options.verbose:
        print "Found no unobsolete patches"
  def run(self):
    for bugnum in positional_args:
      self.do_bug(bugnum)


if __name__ == '__main__':

  if len(sys.argv) < 2:
    printUsage()
    sys.exit(-2)

  command = sys.argv[1]
  args = sys.argv[2:]

  if len(command) > 0 and command[0] == '-':
    args.insert(0, command)
    command = ''

  try:
    int(command)
    args.insert(0, command)
    command = "import"
  except ValueError:
    pass

  global_options = [
#    make_option("-h", "--help", action="help"),
    make_option("-v", "--verbose", action="store_true", dest="verbose"),
    make_option("-q", "--quiet", action="store_false", dest="verbose"),
    make_option("-r", "--dry-run", action="store_true", dest="readonly", help="Don't actually operate on the hg repo"),
    make_option("-b", "--bugzilla", dest="bugzilla", help="specify the bugzilla repository to use")
  ]

  global_defaults = {
    "bugzilla" : os.environ['BUGZILLA'] if 'BUGZILLA' in os.environ else "bugzilla.mozilla.org"
  }

  commands = {
    '' : BaseCommand(),
    "help" : Help(),
    "import" : Import(),
  }

  if command not in commands:
    print "Unknown command %s" % command
    print "Available commands are"
    print ' '.join(commands.keys())
    sys.exit()

  global_options.extend(commands[command].options)
  global_defaults.update(commands[command].defaults)

  parser = OptionParser(commands[command].usage, option_list=global_options)
  parser.set_defaults(**global_defaults)
  options, positional_args = parser.parse_args(args=args)

  commands[command].run()
