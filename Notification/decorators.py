# notifications/decorators.py
from functools import wraps
from .models import NotificationStep, NotificationPreference
from .utils import send_push_notification, send_in_app_message

def notify_step(step_code):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            result = func(*args, **kwargs)

            # Find the step
            try:
                step = NotificationStep.objects.get(code=step_code)
            except NotificationStep.DoesNotExist:
                return result

            # All preferences for this step
            prefs = NotificationPreference.objects.filter(step=step, enabled=True)

            for pref in prefs:
                user = pref.user
                channel = pref.channel

                title = f"رویداد جدید: {step.name}"
                body = f"عملیات مربوط به {step.name} انجام شد."

                if channel in ["push", "both"]:
                    send_push_notification(user, title, body)

                if channel in ["message", "both"]:
                    send_in_app_message(user, title, body)

            return result
        return wrapper
    return decorator
