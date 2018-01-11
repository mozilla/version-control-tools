import urllib2
try:
    import cStringIO as StringIO
except ImportError:
    import StringIO
import os
import re
from itertools import cycle

from mercurial.util import Abort
import bz

# Default behavior is to return all patches smushed together. hg import will
# separate them back out. But for mq, we need a side-channel to transmit them
# separately. The caller will use set_patch_container(somelist), and the import
# process will append all patches to that list.
def set_patch_container(container=None):
    Handler.patch_container = container

class ObjectResponse(object):

    def __init__(self, obj):
        self.obj = obj

    def read(self):
        return self.obj


class Handler(urllib2.BaseHandler):

    patch_container = None

    def __init__(self, ui, passmgr):
        self.ui = ui
        self.passmgr = passmgr

        self.base = ui.config('qimportbz', 'bugzilla',
                              os.environ.get('BUGZILLA', "bugzilla.mozilla.org"))

        if not self.base.startswith(('http://', 'https://')):
            self.base = 'https://%s' % self.base

        self.base = self.base.rstrip('/')

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
        url = "%s/show_bug.cgi?ctype=xml&id=%s" % (self.base, num)
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
            except bz.PermissionError as e:
                self.ui.status("\n")
                raise Abort(e.msg)
            self.ui.status(" done\n")

        attachid = req.get_selector()[1:]
        if not patch and attachid:
            patch = bug.get_patch(attachid)
            if patch is None:
                # Try interpreting attachid as the number of a nonobsolete patch.
                try:
                    patches = [p for p in bug.patches if not p.obsolete]
                    num = int(attachid)
                    patch = patches[num - 1]
                except ValueError, IndexError:
                    pass

        patches = [] if patch is None else [patch]

        if not patches:
            if not bug.patches:
                raise Abort("No patches found for this bug")
            patches = [p for p in bug.patches if not p.obsolete]
            if not patches:
                if 'y' != self.ui.prompt("Only obsolete patches found. Import anyway? [Default is 'y']", default='y'):
                    raise Abort("Nothing to import")
                patches = bug.patches

        if len(patches) > 1:
            patches = self.choose_patches(patches)

        if len(patches) == 0:
            return

        if Handler.patch_container is None:
            return PatchResponse(patches)
        else:
            Handler.patch_container.extend(patches)
            return PatchResponse([patches[0]])

    def choose_patches(self, patches):
        if self.autoChoose:
            return patches
        # The initial sort order is by attachment 'id'.
        sort_types = cycle(['desc', 'id'])
        valid_patch_choices = range(1, len(patches) + 1)
        self.list_patches(patches)
        while True:
            allstr = "1-%d" % len(patches)
            choicestr = self.ui.prompt("\nWhich patches do you want to import, and in which order? [Default is all]\n"
                                       "(eg '1-3,5', or 's' to toggle the sort order between id & patch description)",
                                       default=allstr)
            if choicestr == "s":
                new_sort_type = sort_types.next()
                self.ui.write("\nSorted by %s:\n" % new_sort_type)
                patches.sort(key=lambda p: getattr(p, new_sort_type))
                self.list_patches(patches)
                continue
            elif choicestr == "all":
                choicestr = allstr
            selected_patches = []
            try:
                for choice in map(str.strip, choicestr.split(',')):
                    # The string should either be a range of patches or else a single patch number.
                    m = re.match(r'(\d+)-(\d+)$', choice)
                    if m:
                        start = int(m.group(1))
                        end = int(m.group(2))
                        if start not in valid_patch_choices or end not in valid_patch_choices:
                            raise IndexError()
                        if start < end:
                            selected_patches.extend(patches[start - 1:end])
                        else:
                            # The range is in reverse order, eg "3-1".
                            selected_patches.extend(reversed(patches[end - 1:start]))
                    else:
                        if int(choice) not in valid_patch_choices:
                            raise IndexError()
                        selected_patches.append(patches[int(choice) - 1])
                return selected_patches
            except (ValueError, IndexError):
                self.ui.warn("Invalid patch selection: '%s'\n" % choice)

    def list_patches(self, patches):
        self.ui.write("\n")
        for i, p in enumerate(patches):
            self.ui.write("%s: %s\n" % (i + 1, p.desc), label="cyan")
            flags = p.joinFlags(False)
            if flags:
                self.ui.write("   %s\n" % flags)


# interface reverse engineered from urllib.addbase
class PatchResponse(object):

    def __init__(self, patches):
        # utf-8: convert from internal (16/32-bit) Unicode to 8-bit encoding.
        # NB: Easier output to deal with, as most (code) patches are ASCII only.
        self.fps = [StringIO.StringIO(unicode(p).encode('utf-8')) for p in patches]

    def read(self, size=-1):
        if size < 0:
            return ''.join(p.read() for p in self.fps)
        data = ''
        while size > 0 and self.fps:
            subdata = self.fps[0].read(size)
            if len(subdata) == 0:
                self.fps.pop(0)
                continue
            data += subdata
            size -= len(subdata)
        return data

    def readline(self):
        while self.fps:
            line = self.fps[0].readline()
            if line != '':
                return line
            self.fps.pop(0)
        return ''

    def close(self):
        for fp in self.fps:
            fp.close()

    def fileno(self):
        return None
