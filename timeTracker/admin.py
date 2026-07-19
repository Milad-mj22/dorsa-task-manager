from django.contrib import admin

# Register your models here.
from django.contrib import admin
from .models import Sprint,Story,Task,Team, TimeEntry


admin.site.register(Sprint)
admin.site.register(TimeEntry)
@admin.register(Story)
class StoryAdmin(admin.ModelAdmin):

    # 📌 لیست اصلی
    list_display = (
        'title',
        'description',
        'sprint',
        'team',
        'priority',
        'project'

    )

    # 🔍 جستجو
    search_fields = (
        'title',
        'sprint__name',
        'team__name',

    )

    # 🎯 فیلتر سمت راست
    list_filter = (
        'priority',
        'sprint',
        'team',
    )

    # ✏️ مرتب‌سازی

    # ⚡ فیلدهایی که مستقیم قابل ویرایش‌اند
    list_editable = (
        'priority',
        'project'
    )

    # 🚀 بهینه‌سازی ForeignKey
    raw_id_fields = (
        'sprint',
        'team',
    )

    # 📄 صفحه جزئیات (Form layout)
    fieldsets = (
        ('Basic Info', {
            'fields': ('title', 'priority')
        }),
        ('Planning', {
            'fields': ('sprint', 'team')
        }),

    )

    # 📦 تعداد آیتم در هر صفحه
    list_per_page = 25

admin.site.register(Task)
admin.site.register(Team)