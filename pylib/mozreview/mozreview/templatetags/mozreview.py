from django import template

register = template.Library()


@register.filter()
def isSquashed(aReviewRequest):
    return str(aReviewRequest.extra_data.get('p2rb.is_squashed', 'False')).lower() == 'true'

@register.filter()
def isPush(aReviewRequest):
    return str(aReviewRequest.extra_data.get('p2rb', 'False')).lower() == 'true'
