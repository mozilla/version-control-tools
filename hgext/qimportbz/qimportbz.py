#!/usr/local/bin/python
# Imports patches from bugzilla into the hg repo in the current working directory
import sys, os
import urllib2
import base64
from xml.etree.ElementTree import fromstring as xmlfromstring
from subprocess import Popen, PIPE
import pdb
from optparse import OptionParser, make_option

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

def importPatch(p, patchname):
  data64 = p.find('data').text
  data = base64.b64decode(data64)
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

def getFlagDesc(p):
  descs = []
  for f in p.findall('flag'):
    name = f.attrib['name']
    status = f.attrib['status']
    setter = f.attrib['setter']

    if name == 'review':
      settername = setter[:setter.index('@')]
      descs.append('%s: r%s' % (settername, status))
    elif options.verbose:
      print "Unhandled flag %s" % name
  return ', '.join(descs)

def cleanChoice(c):
  return int(c.strip().strip(',').strip())

def multiplePatchChoose(patches):
  for i,p in enumerate(patches):
    desc = p.find('desc').text
    flags = getFlagDesc(p)
    print "%s: %s %s" % (i+1, desc, flags)
  choicestr = raw_input("Which patches do you want to import? ")
  return [cleanChoice(s)-1 for s in choicestr.split()]

class BaseCommand(object):
  options = []
  defaults = {}
  usage = ""

class Help(BaseCommand):
  usage = "%prog command [options]"
  def run(self):
    parser.print_help()

class Import(BaseCommand):
  options = []
  defaults = {}
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

    def getPatchName(p):
      desc = p.find('desc').text
      return "bug%s_%s" % (bugnum, desc.replace(' ', '_'))

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
    make_option("-r", "--dry-run", action="store_true", dest="readonly"),
    make_option("-b", "--bugzilla", dest="bugzilla")
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
