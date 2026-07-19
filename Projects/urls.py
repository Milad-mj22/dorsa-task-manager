from django.urls import path
from .views import project_time_report,projects_time_summary

urlpatterns = [
    path("spec_proj/<int:project_id>/time/", project_time_report, name="project_time_report"),
    path("time/", projects_time_summary, name="projects_time_summary"),
]