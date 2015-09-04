import urllib
from bugsy import Bugsy


def rest_url(*parts, **kwargs):
    base = '/'.join(['https://bugzilla.mozilla.org/rest'] +
                    [str(p) for p in parts])
    kwargs.setdefault('include_fields', Bugsy.DEFAULT_SEARCH)
    params = urllib.urlencode(kwargs, True)
    if params:
        return '%s?%s' % (base, params)
    return base
