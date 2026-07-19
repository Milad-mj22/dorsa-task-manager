from django import forms
from .models import NotificationPreference, NotificationStep
from django.contrib.auth import get_user_model

User = get_user_model()



class NotificationPreferenceInlineForm(forms.Form):
    """
    This is for a simple page:
    - select user
    - show all steps in a table
    - choose channel + enabled
    """
    user = forms.ModelChoiceField(queryset=User.objects.all(), label="User")


from django import forms
from .models import NotificationStep, NotificationPreference


class NotificationStepForm(forms.ModelForm):
    class Meta:
        model = NotificationStep
        fields = ["code", "name", "description"]




class NotificationPreferenceForm(forms.ModelForm):
    class Meta:
        model = NotificationPreference
        # ⛔ نگیم exclude، بلکه دقیقاً فیلدهایی که می‌خوایم قابل ویرایش باشن رو بنویسیم
        fields = ["enabled", "channel"]