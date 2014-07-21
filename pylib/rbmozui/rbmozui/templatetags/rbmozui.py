from django import template

register = template.Library()


@register.filter()
def isSquashed(aReviewRequest):
    return aReviewRequest.extra_data.get('p2rb.is_squashed', 'False') == 'True'

@register.filter()
def isPush(aReviewRequest):
    return aReviewRequest.extra_data.get('p2rb', 'False') == 'True'
