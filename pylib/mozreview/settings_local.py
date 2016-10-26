# Custom settings_local.py file just for running unit tests.

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    }
}

SECRET_KEY = '1f60zf9t3-zjjms@f5^%(pr3t2&kk9dcg4m@xliz=u$r_9&@6h'
