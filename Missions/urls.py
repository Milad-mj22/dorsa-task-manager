from django.urls import path
from Missions import views
urlpatterns = [
    # ... your other mission URLs
    path('create/', views.mission_create, name='mission_create'),
    path('mission/<int:mission_id>/flow/', views.mission_flow_list, name='mission_flow_list'),
    path('flow/<int:flow_id>/approve/', views.approve_step, name='approve_step'),
    path('missions/', views.mission_list, name='mission_list'),
    path('missions/<int:pk>/', views.mission_detail, name='mission_detail'),
    path('my-approvals/', views.my_pending_approvals, name='my_pending_approvals'),
    path('approve/<int:flow_id>/', views.approve_flow, name='approve_flow'),
]