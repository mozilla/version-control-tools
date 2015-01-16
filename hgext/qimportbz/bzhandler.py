# std python modules
import urllib2
try:
    import cStringIO as StringIO
except ImportError:
    import StringIO
import os
import re

# qimportbz modules
import bz

# Patch list
delayed_imports = []

# The patch that got imported
imported_patch = None


def last_imported_patch():
    return imported_patch


class ObjectResponse(object):
    def __init__(self, obj):
        self.obj = obj

    def read(self):
        return self.obj


class Handler(urllib2.BaseHandler):
    def __init__(self, ui, passmgr):
        self.ui = ui
        self.passmgr = passmgr

        self.base = ui.config('qimportbz', 'bugzilla',
                              os.environ.get('BUGZILLA', "bugzilla.mozilla.org"))

        self.autoChoose = ui.config('qimportbz', 'auto_choose_all', False)

    # Change the request to the https for the bug XML
    def bz_open(self, req):
        num = int(req.get_host())
        if num in bz.cache:
            bug = bz.cache[num]
            # strip the /
            attachid = req.get_selector()[1:]
            if attachid:
                return ObjectResponse(bug.get_patch(attachid))

            return ObjectResponse(bug)

        # Normal case, return a stream of text
        url = "https://%s/show_bug.cgi?ctype=xml&id=%s" % (self.base, num)
        self.ui.status("Fetching...")
        return self.parent.open(url)

    # Once the XML is fetched, parse and decide what to return
    def bz_response(self, req, res):
        patch = None
        # Check if we're doing a cached lookup - no ui in this case since we're
        # working around mq's limitations
        data = res.read()
        if isinstance(data, bz.Bug):
            bug = data
        elif isinstance(data, bz.Patch):
            patch = data
        else:
            # network read
            self.ui.status(" done\n")
            self.ui.status("Parsing...")
            try:
                bug = bz.Bug(self.ui, data)
            # TODO: update syntax when mercurial requires Python 2.6
            except bz.PermissionError, e:
                self.ui.warn(" %s\n" % e.msg)
                return
            self.ui.status(" done\n")

        attachid = req.get_selector()[1:]
        if not patch and attachid:
            patch = bug.get_patch(attachid)

        if not patch:
            patches = [p for p in bug.patches if not p.obsolete]
            if len(patches) == 0:
                patches = bug.patches
                if len(patches) == 0:
                    self.ui.warn("No patches found for this bug\n")
                    return

                if len(patches) > 1:
                    self.ui.warn("Only obsolete patches found\n")
                else:
                    if 'y' != self.ui.prompt("Only found one patch and it is obsolete. Import anyways? [Default is 'y']", default='y'):
                        return
            if len(patches) == 1:
                patch = patches[0]
            elif len(patches) > 0:
                for i, p in enumerate(patches):
                    flags = p.joinFlags(False)
                    self.ui.write("%s: %s%s\n" % (i + 1, p.desc, "\n  %s" % flags if flags else ""))
                choicestr = ' '.join([str(n) for n in xrange(1, len(patches)+1)])
                if not self.autoChoose:
                    choicestr = self.ui.prompt("Which patches do you want to import? [Default is '1', use '1-%d' for all]" %
                                               len(patches), default="1")
                for choice in (s.strip() for t in choicestr.split(',') for s in t.split()):
                    try:
                        m = re.match(r'(\d+)-(\d+)$', choice)
                        if m:
                            delayed_imports.extend([patches[p] for p in xrange(int(m.group(1)) - 1, int(m.group(2)))])
                        else:
                            if int(choice) <= 0:
                                raise IndexError()
                            delayed_imports.append(patches[int(choice) - 1])
                    except (ValueError, IndexError):
                        self.ui.warn("Invalid patch number = '%s'\n" % choice)
                        continue
                if not patch and len(delayed_imports) > 0:
                    patch = delayed_imports.pop()

        # and finally return the response
        if patch:
            global imported_patch
            imported_patch = patch
            return PatchResponse(patch)


# interface reverse engineered from urllib.addbase
class PatchResponse(object):
    def __init__(self, p):
        self.patch = p
        # utf-8: convert from internal (16/32-bit) Unicode to 8-bit encoding.
        # NB: Easier output to deal with, as most (code) patches are ASCII only.
        self.fp = StringIO.StringIO(unicode(p).encode('utf-8'))
        self.read = self.fp.read
        self.readline = self.fp.readline
        self.close = self.fp.close

    def fileno(self):
        return None
