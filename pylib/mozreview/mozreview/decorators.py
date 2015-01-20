from djblets.util.decorators import simple_decorator

@simple_decorator
def if_ext_enabled(fn):
    """Only execute the function if the extension is enabled.

    An extension kwarg is expected when calling the decorated function, which
    will be used for the settings.enabled check. All SignalHook handlers can
    expect an extension kwarg which is the primary use case of this decorator.

    MozReview settings has an `enabled` field which controls if the extension
    should send out notifications to Mozilla Pulse. This decorator will check
    the setting and only execute the function if enabled is True.
    """
    def _wrapped(*args, **kwargs):
        ext = kwargs.get('extension', None)

        if ext is None:
            return

        if not ext.settings.get('enabled', False):
            return

        return fn(*args, **kwargs)

    return _wrapped
