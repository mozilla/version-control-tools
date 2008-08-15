#!/usr/local/bin/python
# Imports patches from bugzilla into the hg repo in the current working directory
import sys, os
import urllib2
import base64
from xml.etree.ElementTree import fromstring as xmlfromstring
from subprocess import Popen, PIPE
import pdb

def printUsage():
  print "Usage: qimportbz bug-number"

if len(sys.argv) < 2:
  printUsage()
  sys.exit(-2)

def isGoodAttachment(a):
  if "0" == a.attrib['ispatch']: return False
  id = a.find('attachid').text
  desc = a.find('desc').text
  #print "Found patch %s (%s)" % (id, desc)
  isobsolete = int(a.attrib['isobsolete'])
  if isobsolete:
    #print "...but it was obsolete"
    return False
  return True

def importPatch(p):
  data64 = p.find('data').text
  data = base64.b64decode(data64)
  attachid = p.find('attachid').text
  args = ["hg", "qimport", "-n", "bug%s_%s" % (bugnum, attachid), "-"]
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
    else:
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
  choices = [cleanChoice(s) for s in choicestr.split()]
  #choicestr = raw_input("Import as separate patches (y/n)? ")
  #separatePatches = 'y' in choicestr.lower()
  for choice in choices:
    importPatch(patches[choice-1])

bugzilla_base = os.environ['BUGZILLA'] if 'BUGZILLA' in os.environ else "bugzilla.mozilla.org"
bugnum = sys.argv[1]

url = "https://%s/show_bug.cgi?ctype=xml&id=%s" % (bugzilla_base, bugnum)
print ("Fetching from %s..." % url),
stream = urllib2.urlopen(url)
data = stream.read()
print "\bdone"
#print "Got %s bytes of data" % len(data)
print "Parsing bug...",
xml = xmlfromstring(data)
print "\bdone"
attachments = xml.findall("bug/attachment")
patches = [a for a in attachments if isGoodAttachment(a)]

if len(patches) == 1:
  importPatch(patches[0])
elif len(patches) > 1:
  print "Found multiple patches"
  multiplePatchChoose(patches)
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
  print "Found no unobsolete patches"
