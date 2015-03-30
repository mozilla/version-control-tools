import sys
import logging
logging.basicConfig(stream=sys.stderr, level=logging.DEBUG)
sys.path.insert(0, '/home/ubuntu/version-control-tools/autoland/autoland')

from autoland_rest import app as application
