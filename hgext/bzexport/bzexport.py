import sys
import os.path
from mercurial import extensions

# Redirect to __init__.py
myfile = sys.modules['hgext_bzexport'].__file__
extensions.loadpath(os.path.dirname(myfile), 'hgext.bzexport')
