# notifications/utils.py

from .models import NotificationPreference, NotificationStep
from pywebpush import webpush, WebPushException
import json
from django.conf import settings


def send_push_notification_to_user(user, title, body, extra_data=None):
    """
    ارسال Web Push برای یک کاربر.
    خروجی: (success: bool, error_code: str | None)

    error_code می‌تونه این‌ها باشه:
      - "no_subscription"
      - "invalid_subscription"
      - "other_error"
    """

    # 1) پروفایل و سابسکریپشن
    profile = getattr(user, "profile", None)
    if not profile or not profile.push_endpoint:
        return False, "no_subscription"

    # 2) ساخت payload
    payload = {
        "title": title,
        "body": body,
    }

    if extra_data and "url" in extra_data:
        extra_data["url"] = extra_data["url"].rstrip("/")

    if extra_data and isinstance(extra_data, dict):
        payload.update(extra_data)

    try:
        webpush(
            subscription_info={
                "endpoint": profile.push_endpoint,
                "keys": {
                    "p256dh": profile.push_p256dh,
                    "auth": profile.push_auth,
                },
            },
            data=json.dumps(payload, ensure_ascii=False),
            vapid_private_key=settings.VAPID_PRIVATE_KEY,
            vapid_claims={"sub": settings.VAPID_ADMIN_EMAIL},
        )
        return True, None

    except WebPushException as ex:
        msg = str(ex)

        # اگر response و status_code داشته باشه
        if getattr(ex, "response", None) is not None:
            status = getattr(ex.response, "status_code", None)
            if status in [404, 410]:
                # سابسکریپشن دیگه معتبر نیست → پاکش کن
                profile.push_endpoint = None
                profile.push_p256dh = None
                profile.push_auth = None
                profile.save()
                return False, "invalid_subscription"

        # اگر داخل متن خطا 410 یا unsubscribed بود
        if "410" in msg or "unsubscribed or expired" in msg:
            profile.push_endpoint = None
            profile.push_p256dh = None
            profile.push_auth = None
            profile.save()
            return False, "invalid_subscription"

        # بقیه خطاها
        return False, "other_error"
    



def send_in_app_message(user, title, body, extra=None):
    """
    If you have a Message model or use Django messages framework,
    do something here. For now, it's just a placeholder.
    """
    # Example with custom model:
    # Message.objects.create(user=user, title=title, body=body, data=extra)
    pass



# notifications/utils.py

from .models import NotificationStep, NotificationPreference

def notify_users_for_step(step_code, title, body, extra_data=None):
    try:
        step = NotificationStep.objects.get(code=step_code)
    except NotificationStep.DoesNotExist:
        return

    prefs = NotificationPreference.objects.filter(step=step, enabled=True)

    for pref in prefs:
        user = pref.user

        payload_extra = extra_data or {}
        # مثلا اگر بخوای برای هر کاربر چیز اضافه بفرستی، اینجا می‌تونی دستکاری کنی

        if pref.channel in ["push", "both"]:
            send_push_notification_to_user(
                user,
                title=title,
                body=body,
                extra_data=payload_extra
            )

        if pref.channel in ["message", "both"]:
            send_in_app_message(pref.user, title, body)



def send_webpush(request,code: str = NotificationStep.code ,title:str='',body:str='',url:str='/'):
        try:
            orders_url = request.build_absolute_uri(url)
            
            notify_users_for_step(
                code,
                title=title,
                body = body,
                extra_data={
                    "url": orders_url
                }
            )
        except:
            print('Error in send notification')
