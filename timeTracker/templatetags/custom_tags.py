from django import template
from jalali_date import datetime2jalali
from datetime import date, datetime



register = template.Library()

@register.filter
def get_item(dictionary, key):
    return dictionary.get(key)






@register.filter
def to_jalali(value):
    if isinstance(value, str):
        try:
            # تلاش برای تبدیل رشته به datetime
            value = datetime.strptime(value, '%Y-%m-%d')
        except ValueError:
            return ''  # اگر فرمت اشتباه بود، برگرد رشته خالی

    if isinstance(value, (datetime, date)):
        return datetime2jalali(value).strftime('%Y/%m/%d')
    
    return ''


@register.filter
def as_widget(field, css_class_name):
    return field.as_widget(attrs={'class': css_class_name})
