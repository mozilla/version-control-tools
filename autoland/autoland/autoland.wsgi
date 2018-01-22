import logging
import os
import sys

logging.basicConfig(stream=sys.stderr, level=logging.DEBUG)
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from autoland_rest import app as application
