from django.contrib import admin

# Register your models here.
from .models import Project , City

admin.site.register(Project)
admin.site.register(City)