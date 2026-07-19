from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required, user_passes_test

# Create your views here.
from django.forms import modelformset_factory

from .models import NotificationPreference, NotificationStep
from .forms import NotificationPreferenceForm


def is_staff(user):
    return user.is_staff or user.is_superuser


@login_required
@user_passes_test(is_staff)
def manage_notifications(request, user_id=None):
    """
    Page to manage ONE user's preferences for ALL steps.
    You can link this from admin menu or somewhere.
    """
    from django.contrib.auth import get_user_model
    User = get_user_model()

    user = get_object_or_404(User, id=user_id)

    # Ensure all steps have a preference row for this user
    steps = NotificationStep.objects.all()
    for step in steps:
        NotificationPreference.objects.get_or_create(user=user, step=step)

    PreferenceFormSet = modelformset_factory(
        NotificationPreference,
        form=NotificationPreferenceForm,
        extra=0
    )

    qs = NotificationPreference.objects.filter(user=user).select_related("step")

    if request.method == "POST":
        formset = PreferenceFormSet(request.POST, queryset=qs)
        if formset.is_valid():
            formset.save()
            return redirect("manage_notifications", user_id=user.id)
    else:
        formset = PreferenceFormSet(queryset=qs)

    return render(request, "notifications/manage_notifications.html", {
        "user_obj": user,
        "formset": formset,
    })




User = get_user_model()


@login_required
@user_passes_test(is_staff)
def notification_user_list(request):
    """
    Show all users. When admin clicks a user,
    they go to manage_notifications(user_id).
    """
    users = User.objects.all()
    return render(request, "notifications/user_list.html", {"users": users})





from django.shortcuts import render, redirect, get_object_or_404
from django.forms import modelformset_factory
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth import get_user_model

from .models import NotificationStep, NotificationPreference
from .forms import NotificationStepForm, NotificationPreferenceForm


@login_required
@user_passes_test(is_staff)
def notification_step_list(request):
    steps = NotificationStep.objects.all().order_by("code")
    return render(request, "notifications/step_list.html", {"steps": steps})


@login_required
@user_passes_test(is_staff)
def notification_step_create(request):
    if request.method == "POST":
        form = NotificationStepForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect("notification_step_list")
    else:
        form = NotificationStepForm()

    return render(request, "notifications/step_form.html", {"form": form})



@login_required
@user_passes_test(is_staff)
def notification_step_assign_users(request, step_id):
    step = get_object_or_404(NotificationStep, id=step_id)

    users = User.objects.all()

    # 1) برای هر کاربر یک ردیف تنظیمات بساز (اگر وجود نداشت)
    for u in users:
        NotificationPreference.objects.get_or_create(
            user=u,
            step=step,
            defaults={"enabled": False, "channel": NotificationPreference.CHANNEL_NONE},
        )

    PreferenceFormSet = modelformset_factory(
        NotificationPreference,
        form=NotificationPreferenceForm,
        extra=0,
    )

    qs = NotificationPreference.objects.filter(step=step).select_related("user")

    if request.method == "POST":
        formset = PreferenceFormSet(request.POST, queryset=qs)
        if formset.is_valid():
            # 2) فقط enabled و channel را ذخیره کن، user و step دست نمی‌زنیم
            instances = formset.save(commit=False)
            for obj in instances:
                # obj.user و obj.step از قبل روی instance هستن، فقط همون رو نگه می‌داریم
                obj.save()
            # اگر delete فعال نباشد نیازی به formset.save_m2m نیست
            return redirect("notification_step_assign_users", step_id=step.id)
    else:
        formset = PreferenceFormSet(queryset=qs)

    return render(request, "notifications/step_assign_users.html", {
        "step": step,
        "formset": formset,
    })



@login_required
@user_passes_test(is_staff)
def notification_step_delete(request, step_id):
    step = get_object_or_404(NotificationStep, id=step_id)

    if request.method == "POST":
        step.delete()
        return redirect("notification_step_list")

    return redirect("notification_step_list")
