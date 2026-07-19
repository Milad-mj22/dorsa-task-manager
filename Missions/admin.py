from django.contrib import admin

from Missions.models import FlowStepTemplate, FlowTemplate, Mission, MissionApproval, MissionComment, MissionFlow, MissionType

# Register your models here.


admin.site.register(MissionFlow)
admin.site.register(MissionApproval)
admin.site.register(MissionType)
admin.site.register(Mission)
admin.site.register(MissionComment)
admin.site.register(FlowTemplate)
admin.site.register(FlowStepTemplate)