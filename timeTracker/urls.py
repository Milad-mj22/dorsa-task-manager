from django.urls import path

from django.conf import settings
from django.conf.urls.static import static
from timeTracker import views
from timeTracker.views import api_tasks_load_more, api_update_task_status, dashboard, debug_send_reminder , delete_task, export_tasks_report_excel,  sprint_create, sprint_edit, sprint_list, story_create, story_delete, story_edit, story_list, task_create, task_detail_modal, task_list


urlpatterns = [
    path('', dashboard, name='users-home'),
    # path('register/', RegisterView.as_view(), name='users-register'),
    path('teams/', views.team_list, name='team_list'),
    path('teams/create/', views.team_create, name='team_create'),
    path('teams/<int:pk>/edit/', views.team_edit, name='team_edit'),
    path('sprints/', sprint_list, name='sprint_list'),
    path('sprints/create/', sprint_create, name='sprint_create'),
    path('sprint/<int:sprint_id>/edit/', sprint_edit, name='sprint_edit'),
    path('tasks/create/', task_create, name='task_create'),
    path('stories/', story_list, name='story_list'),
    path('stories/create/', story_create, name='story_create'),
    path('stories/<int:pk>/edit/', story_edit, name='story_edit'),
    path('stories/<int:pk>/delete/', story_delete, name='story_delete'),
    path('tasks/', task_list, name='task_list'),
    path('tasks/<int:pk>/status/', api_update_task_status, name='api_update_task_status'),
    path('tasks/<int:pk>/modal/', task_detail_modal, name='task_detail_modal'),
    path('tasks/delete/<int:task_id>/', delete_task, name='delete_task'),
    path("tasks/load-more/", api_tasks_load_more, name="tasks_load_more"),
    path('time_entry/delete/<int:entry_id>/', views.delete_time_entry, name='delete_time_entry'),

    path('assign_stories_to_project/', views.assign_stories_to_project, name='assign_stories_to_project'),
    path('select_sprint/', views.select_sprint, name='select_sprint'),


    path('export/tasks-excel/', export_tasks_report_excel, name='export_tasks_excel'),
    
    path('debug-send-reminder/', debug_send_reminder, name='debug_send_reminder'),


]+ static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)