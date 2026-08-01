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

admin.site.register(Team)





@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    # List display fields
    list_display = (
        'id',
        'title',
        'priority',
        'status',
        'assigned_to',
        'goal_time',
        'story',
        'wbs_row',
        'created_at',
        'is_delete'
    )
    
    # Filters
    list_filter = (
        'status',
        'priority',
        'assigned_to',
        'story',
        'is_delete',
        'created_at'
    )
    
    # Search fields
    search_fields = (
        'title',
        'description',
        'wbs_row',
        'assigned_to__username',
        'assigned_to__email'
    )
    
    # Default ordering
    ordering = ('-priority', 'status', 'created_at')
    
    # Read-only fields
    readonly_fields = ('created_at',)
    
    # Fieldsets for detail view
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'description', 'story', 'wbs_row')
        }),
        ('Assignment & Progress', {
            'fields': ('assigned_to', 'status', 'priority')
        }),
        ('Time Management', {
            'fields': ('goal_time',)
        }),
        ('System Fields', {
            'fields': ('created_at', 'is_delete', 'user_delete'),
            'classes': ('collapse',)
        }),
    )
    
    # Actions
    actions = ['mark_as_done', 'mark_as_doing', 'mark_as_todo', 'delete_selected']
    
    def mark_as_done(self, request, queryset):
        queryset.update(status='done')
        self.message_user(request, f"{queryset.count()} task(s) marked as Done.")
    mark_as_done.short_description = "Mark selected tasks as Done"
    
    def mark_as_doing(self, request, queryset):
        queryset.update(status='doing')
        self.message_user(request, f"{queryset.count()} task(s) marked as Doing.")
    mark_as_doing.short_description = "Mark selected tasks as Doing"
    
    def mark_as_todo(self, request, queryset):
        queryset.update(status='todo')
        self.message_user(request, f"{queryset.count()} task(s) marked as To Do.")
    mark_as_todo.short_description = "Mark selected tasks as To Do"
    
    # Custom method for priority display
    def priority_display(self, obj):
        return '★' * obj.priority if obj.priority else '-'
    priority_display.short_description = 'Priority'
    
    # Override delete method to soft delete
    def delete_queryset(self, request, queryset):
        for obj in queryset:
            obj.is_delete = True
            obj.user_delete = request.user
            obj.save()
    delete_queryset.short_description = "Soft delete selected tasks"
    
    # Override get_queryset to show only non-deleted by default
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if not request.GET.get('show_deleted'):
            return qs.filter(is_delete=False)
        return qs


# Optional: Inline admin for Task within Story
class TaskInline(admin.TabularInline):
    model = Task
    extra = 0
    fields = ('title', 'status', 'assigned_to', 'priority', 'goal_time')
    show_change_link = True

