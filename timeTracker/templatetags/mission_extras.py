from django import template

register = template.Library()

@register.filter
def get_approval_for_user(approvals, user):
    return approvals.filter(user=user).first()



@register.filter
def as_widget(field, attrs):
    return field.as_widget(attrs=attrs)
