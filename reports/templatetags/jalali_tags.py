from django import template
from django.utils import timezone
import jdatetime

register = template.Library()

@register.filter
def jalali(value, format='%d %B %Y'):
    """Convert Gregorian date to Jalali"""
    if not value:
        return ''
    
    # If it's a datetime, convert to date
    if hasattr(value, 'date'):
        value = value.date()
    
    try:
        # Convert to jalali
        jalali_date = jdatetime.date.fromgregorian(date=value)
        return jalali_date.strftime(format)
    except:
        return value

@register.filter
def jalali_day(value):
    """Get Jalali day number"""
    if not value:
        return ''
    try:
        jalali_date = jdatetime.date.fromgregorian(date=value)
        return jalali_date.day
    except:
        return ''

@register.filter
def jalali_month_short(value):
    """Get short Jalali month name"""
    if not value:
        return ''
    try:
        jalali_date = jdatetime.date.fromgregorian(date=value)
        months = ['فر', 'ار', 'خر', 'تی', 'مر', 'شه', 'مه', 'آب', 'آذ', 'دی', 'بف', 'اسف']
        return months[jalali_date.month - 1]
    except:
        return ''