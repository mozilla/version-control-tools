from djblets.util.decorators import simple_decorator
from djblets.webapi.decorators import (_find_httprequest,
                                       webapi_decorator,
                                       webapi_login_required,
                                       webapi_response_errors)
from djblets.webapi.errors import PERMISSION_DENIED


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

        if not ext.get_settings('enabled', False):
            return

        return fn(*args, **kwargs)

    return _wrapped


def webapi_scm_groups_required(*groups):
    """Checks that a user has required scm ldap groups."""
    @webapi_decorator
    def _dec(view_func):

        @webapi_login_required
        @webapi_response_errors(PERMISSION_DENIED)
        def _check_groups(*args, **kwargs):
            request = _find_httprequest(args)
            mrp = request.mozreview_profile

            if not mrp:
                # This should never happen since webapi_login_required
                # should mean they are authenticated and our middleware
                # has added the profile to the request. Check it just
                # to make sure nothing went wrong with the middleware.
                logging.error('No MozReviewUserProfile for authenticated user')
                return PERMISSION_DENIED

            if not mrp.ldap_username:
                return PERMISSION_DENIED.with_message(
                    'You are not associated with an ldap account')

            for group in groups:
                if not mrp.has_scm_ldap_group(group):
                    return PERMISSION_DENIED.with_message(
                        'You do not have the required ldap permissions')

            return view_func(*args, **kwargs)

        return _check_groups

    return _dec
