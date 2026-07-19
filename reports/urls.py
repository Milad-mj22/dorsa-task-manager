
from django.urls import path

from django.conf import settings
from django.conf.urls.static import static
from .views import data_dashboard_view, selective_dashboard, team_dashboard, team_overview_view, team_timeline_view, users_task_dashboard


urlpatterns = [

    path('team_dashboard/',team_dashboard , name='team_dashboard'),
    path('selective_dashboard/',selective_dashboard , name='selective_dashboard'),
    path('data_dashboard/',data_dashboard_view , name='data_dashboard'),
    path('team-overview/', team_overview_view, name='team_overview'),  # ✅ new
    path('team-timeline/', team_timeline_view, name='team_timeline'),
    path('users_task_dashboard/', users_task_dashboard, name='users_task_dashboard'),


]+ static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)





