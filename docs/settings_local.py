import os

SECRET_KEY = 'foobar'
CACHE_BACKEND = 'locmem://'
LOCAL_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), 'data'))
ADMINS = [
    ('Example Admin', 'admin@example.com'),
]
