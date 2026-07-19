
from django.urls import path
from Notification import views


from django.urls import path

from django.conf import settings
from django.conf.urls.static import static


urlpatterns = [
    path("users/", views.notification_user_list, name="notification_user_list"),
    path("manage/<int:user_id>/", views.manage_notifications, name="manage_notifications"),

    path("", views.notification_step_list, name="notification_step_list"),
    path("steps/add/", views.notification_step_create, name="notification_step_create"),
    path(
        "steps/<int:step_id>/assign-users/",
        views.notification_step_assign_users,
        name="notification_step_assign_users",
    ),
    path("steps/<int:step_id>/delete/", views.notification_step_delete, name="notification_step_delete"),



]+ static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)