from django.shortcuts import render

from Projects.models import Project
from otp_manager.models import OTPVar_Enum, SMS_Recievers, SMS_Template, SMSServiceTemplate_Enum
from otp_manager.service import send_sms
from users.views import convert_georgian2jalali, convert_to_jalali

# Create your views here.
def is_any_team_admin(user):
    return hasattr(user, 'profile') and user.profile.admin_teams.exists()

def dashboard(request):
    return render(request, 'dashboard.html', {
        'user_data': request.user})



# timeTracker/views.py

from django.shortcuts import render, redirect, get_object_or_404
from .models import Sprint, Story, Task, Team, TimeEntry
from .forms import SprintForm, StoryForm, TaskForm, TeamForm, TimeEntryForm
from django.contrib.auth.decorators import login_required, user_passes_test

def is_superuser(user):
    return user.is_superuser  # or use any custom logic

@login_required
def team_list(request):
    teams = Team.objects.all()
    return render(request, 'teams/team_list.html', {'teams': teams})

@login_required
def team_create(request):
    if request.method == 'POST':
        form = TeamForm(request.POST)
        if form.is_valid():
            team = form.save(commit=False)  # Delay save
            team.save()                    # Save the instance first
            form.save_m2m()                # Now save M2M fields
            return redirect('team_list')
    else:
        form = TeamForm()
    return render(request, 'teams/team_form.html', {'form': form, 'title': 'Create Team'})

@login_required
def team_edit(request, pk):
    team = get_object_or_404(Team, pk=pk)
    form = TeamForm(request.POST or None, instance=team)
    if request.method == 'POST' and form.is_valid():
        team = form.save(commit=False)  # Delay save
        team.save()                    # Save the instance first
        form.save_m2m() 

                    # Explicitly sync admin_teams of each profile (optional)
        for profile in form.cleaned_data['admins']:
            profile.profile.admin_teams.add(team)


        return redirect('team_list')
    return render(request, 'teams/team_form.html', {'form': form, 'title': 'Edit Team'})




@login_required
# @user_passes_test(is_any_team_admin)
def sprint_list(request):
    sprints = Sprint.objects.all().order_by('-start_date')
    return render(request, 'sprints/sprint_list.html', {'sprints': sprints})


@login_required
def sprint_create(request):
    if request.method == 'POST':
        form = SprintForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('sprint_list')
    else:
        form = SprintForm()

    return render(request, 'sprints/sprint_form.html', {
        'form': form,
        'title': 'Create Sprint'
    })


@login_required
def sprint_edit(request, sprint_id):
    sprint = get_object_or_404(Sprint, id=sprint_id)

    if request.method == 'POST':
        form = SprintForm(request.POST, instance=sprint)
        if form.is_valid():
            form.save()
            return redirect('sprint_list')  # Redirect back to the sprint list after saving
    else:
        form = SprintForm(instance=sprint)

    return render(request, 'sprints/sprint_edit.html', {'form': form, 'sprint': sprint})


@login_required
def task_create(request):
    profile = request.user.profile
    admin_teams = profile.admin_teams.all()

    # Filter stories to only those in admin's teams
    allowed_stories = Story.objects.filter(team__in=admin_teams)
    allowed_stories = allowed_stories.exclude(
        title__in=["nan", "NaN", "NAN", ""]
    ).exclude(title__isnull=True)

    if request.method == 'POST':
        form = TaskForm(request.POST)
        form.fields['story'].queryset = allowed_stories  # Ensure correct filtering on POST

        if form.is_valid():
            story = form.cleaned_data['story']
            if story.team in admin_teams:
                task = form.save()
                return redirect('task_list')  # Create this view later
            else:
                return render(request, '403.html')  # Not authorized for this story
    else:
        form = TaskForm()
        form.fields['story'].queryset = allowed_stories  # Only allow stories in admin’s teams

    return render(request, 'tasks/task_form.html', {'form': form, 'title': 'Create Task'})







@login_required
def story_list(request):
    profile = request.user.profile
    admin_teams = profile.admin_teams.all()

    team_id = request.GET.get('team')
    selected_team = None

    if team_id:
        selected_team = admin_teams.filter(id=team_id).first()
        if selected_team:
            stories = Story.objects.filter(team=selected_team).select_related('sprint', 'team')
        else:
            stories = Story.objects.none()
    else:
        stories = Story.objects.filter(team__in=admin_teams).select_related('sprint', 'team')

    return render(request, 'stories/story_list.html', {
        'stories': stories,
        'admin_teams': admin_teams,
        'selected_team': selected_team,
    })

@login_required
def story_create(request):
    profile = request.user.profile
    admin_teams = profile.admin_teams.all()

    if request.method == 'POST':
        form = StoryForm(request.POST)
        form.fields['team'].queryset = admin_teams
        if form.is_valid():
            story = form.save(commit=False)
            if story.team in admin_teams:
                story.save()
                return redirect('story_list')
            return render(request, '403.html')
    else:
        form = StoryForm()
        form.fields['team'].queryset = admin_teams

    return render(request, 'stories/story_form.html', {'form': form, 'title': 'Create Story'})

@login_required
def story_edit(request, pk):
    profile = request.user.profile
    story = get_object_or_404(Story, pk=pk)

    if story.team not in profile.admin_teams.all():
        return render(request, '403.html')

    form = StoryForm(request.POST or None, instance=story)
    form.fields['team'].queryset = profile.admin_teams.all()

    if request.method == 'POST' and form.is_valid():
        story = form.save(commit=False)
        story.save()
        return redirect('story_list')

    return render(request, 'stories/story_form.html', {'form': form, 'title': 'Edit Story'})

@login_required
def story_delete(request, pk):
    profile = request.user.profile
    story = get_object_or_404(Story, pk=pk)

    if story.team not in profile.admin_teams.all():
        return render(request, '403.html')

    if request.method == 'POST':
        story.delete()
        return redirect('story_list')

    return render(request, 'stories/story_confirm_delete.html', {'story': story})



def _get_filtered_tasks_queryset(request):
    """بر اساس پروفایل کاربر و فیلترهای فرم، queryset مناسب را برمی‌گرداند."""
    profile = request.user.profile
    teams = profile.teams.all()

    qs = Task.objects.filter(
        story__team__in=teams,
        story__sprint__is_active=True,
        is_delete=False,
    ).select_related(
        'story',
        'assigned_to',
        'story__team',
        'story__sprint',
    ).order_by('-id')

    team_id = request.GET.get('team')
    user_id = request.GET.get('user')
    sprint_id = request.GET.get('sprint')
    priority = request.GET.get('priority')

    if team_id:
        qs = qs.filter(story__team_id=team_id)
    if user_id:
        qs = qs.filter(assigned_to_id=user_id)
    if sprint_id:
        qs = qs.filter(story__sprint_id=sprint_id)
    if priority:
        qs = qs.filter(priority=priority)

    return qs, teams


from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.shortcuts import render
from django.core.paginator import Paginator

@login_required
def task_list(request):
    profile = request.user.profile
    print('milad*-80')
    tasks_qs, teams = _get_filtered_tasks_queryset(request)

    users = User.objects.filter(profile__teams__in=teams).distinct()
    sprints_qs = Sprint.objects.filter(story__team__in=teams, is_active=True).distinct()

    selected_team_id = request.GET.get('team')
    selected_user_id = request.GET.get('user')
    selected_sprint_id = request.GET.get('sprint')   # may be None
    selected_priority = request.GET.get('priority')

    # ✅ AUTO-SELECT last sprint if not provided
    if not selected_sprint_id:
        # Prefer ordering by a real date field if you have it
        # Use whatever you actually have: end_date, start_date, created_at, etc.
        last_sprint = (
            sprints_qs.order_by('-start_date', '-id').first()
            # or: sprints_qs.order_by('-end_date', '-id').first()
            # or: sprints_qs.order_by('-created_at', '-id').first()
            # fallback: sprints_qs.order_by('-id').first()
        )
        if last_sprint:
            selected_sprint_id = str(last_sprint.id)
            # ✅ Apply the default filter to tasks
            tasks_qs = tasks_qs.filter(story__sprint_id=last_sprint.id)

    # The sprints list for dropdown (keep as queryset or list)
    sprints = sprints_qs

    full_mode = True
    page_number = 1

    if not full_mode:
        page_size = 30
        paginator = Paginator(tasks_qs, page_size)
        tasks_page = paginator.page(page_number)

        tasks = tasks_page.object_list
        has_more = tasks_page.has_next()
    else:
        tasks = tasks_qs
        has_more = False

    return render(request, 'tasks/task_list.html', {
        'tasks': tasks,
        'teams': teams,
        'users': users,
        'sprints': sprints,
        'selected_team_id': selected_team_id,
        'selected_user_id': selected_user_id,
        'selected_sprint_id': selected_sprint_id,  # ✅ now set automatically
        'selected_priority': selected_priority,
        'title': 'Task Board',
        'current_page': page_number,
        'has_more': has_more,
    })



from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt


@login_required
def api_update_task_status(request, pk):
    try:
        task = Task.objects.get(pk=pk)
    except Task.DoesNotExist:
        return JsonResponse({'error': 'Task not found'}, status=404)
    user = request.user
    is_assigned = (task.assigned_to_id == user.id)
    # Validate that user belongs to the team
    if request.user.profile not in task.story.team.members.all() :
        return JsonResponse({'error': 'Permission denied'}, status=403)

    if not is_assigned :
        return JsonResponse({'error': 'این وظیفه برای شما تعریف نشده است.'}, status=403)


    new_status = request.POST.get('status')
    if new_status not in ['todo', 'doing', 'done']:
        return JsonResponse({'error': 'Invalid status'}, status=400)
    old_status = task.status
    task.status = new_status
    task.save()

    # Get the total hours for a specific task
    total_hours = TimeEntry.objects.filter(task=task).aggregate(Sum('hours_spent'))['hours_spent__sum']

    # If no entries exist, the result will be None, so handle it:
    if total_hours is None:
        total_hours = 0

    total_hours = int(float(total_hours))

    sms_template = SMS_Template.objects.filter(name =SMSServiceTemplate_Enum.TASK_MANAGER )
    if sms_template.exists():
        sms_template = sms_template.first()
        recievers = SMS_Recievers.objects.filter(template=sms_template)
        for r in recievers:
            task_name = f'{task.story.title} : {task.title}'
            user_name = f'{user.profile.first_name} {user.profile.last_name}'
            goal_time = f'{str(int(float(task.goal_time)))} ساعت'
            ret = send_sms(sms_template,phone_number=r.persons.phone,vars={OTPVar_Enum.TITLE:task.title,OTPVar_Enum.NAME:user_name,OTPVar_Enum.OLDSTATUS:old_status,OTPVar_Enum.NEWSTATUS:new_status,OTPVar_Enum.HOUR:goal_time,OTPVar_Enum.HOUR2:total_hours,})
            print(ret)



    return JsonResponse({'success': True, 'task_id': task.id, 'new_status': task.status})

from django.core.paginator import Paginator, EmptyPage
from django.http import JsonResponse
from django.template.loader import render_to_string
from django.contrib.auth.decorators import login_required

@login_required
def api_tasks_load_more(request):
    page = int(request.GET.get("page", 1))
    page_size = 30

    tasks_qs, _ = _get_filtered_tasks_queryset(request)

    paginator = Paginator(tasks_qs, page_size)

    try:
        tasks_page = paginator.page(page)
    except EmptyPage:
        return JsonResponse({
            "todo_html": "",
            "doing_html": "",
            "done_html": "",
            "has_more": False
        })

    tasks = tasks_page.object_list

    todo_html = render_to_string(
        "tasks/partials/tasks_items_todo.html",
        {"tasks": tasks},
        request=request,
    )
    doing_html = render_to_string(
        "tasks/partials/tasks_items_doing.html",
        {"tasks": tasks},
        request=request,
    )
    done_html = render_to_string(
        "tasks/partials/tasks_items_done.html",
        {"tasks": tasks},
        request=request,
    )

    return JsonResponse({
        "todo_html": todo_html,
        "doing_html": doing_html,
        "done_html": done_html,
        "has_more": tasks_page.has_next(),
    })




@login_required
def task_detail_modal(request, pk):
    task = get_object_or_404(Task, pk=pk)
    user = request.user

    is_assigned = (task.assigned_to_id == user.id)
    is_team_admin = task.story.team.admins.filter(id=user.id).exists()
    is_super = user.is_superuser

    # Only these users can log time / see full modal
    has_permission = is_assigned or is_team_admin or is_super

    if request.method == 'POST':
        if not has_permission:
            return JsonResponse(
                {'error': 'شما مجاز به ثبت زمان برای این تسک نیستید.'},
                status=403
            )

        form = TimeEntryForm(request.POST)

        if form.is_valid():
            # already validated hours ≤ 32 in form
            doing_date_str = request.POST.get('doing_date', '').strip()

            if not doing_date_str:
                form.add_error(None, 'لطفاً تاریخ انجام را انتخاب کنید.')
            else:
                try:
                    gregorian_dt = convert_georgian2jalali(doing_date_str)
                except Exception:
                    form.add_error(None, 'تاریخ وارد شده نامعتبر است.')

            if form.errors:
                # Re-render modal content with errors
                entries = TimeEntry.objects.filter(task=task).order_by('-datetime')
                html = render_to_string(
                    'tasks/partials/task_modal_content.html',
                    {
                        'task': task,
                        'form': form,
                        'entries': entries,
                        'user': user,   # needed in template
                    },
                    request=request,
                )
                return JsonResponse({'html': html}, status=400)

            # All good → save entry
            entry = form.save(commit=False)
            entry.task = task
            entry.user = user
            entry.datetime = gregorian_dt    # save Gregorian datetime
            entry.save()

            # reset form after save
            form = TimeEntryForm()
        else:
            # invalid form (e.g. hours_spent)
            entries = TimeEntry.objects.filter(task=task).order_by('-datetime')
            html = render_to_string(
                'tasks/partials/task_modal_content.html',
                {
                    'task': task,
                    'form': form,
                    'entries': entries,
                    'user': user,
                },
                request=request,
            )
            return JsonResponse({'html': html}, status=400)

    else:
        # GET
        form = TimeEntryForm()

    # Build HTML for permitted / not permitted users
    if has_permission:
        entries = TimeEntry.objects.filter(task=task).order_by('-datetime')
        html = render_to_string(
            'tasks/partials/task_modal_content.html',
            {
                'task': task,
                'form': form,
                'entries': entries,
                'user': user,
            },
            request=request,
        )
    else:
        html = render_to_string(
            "tasks/partials/no_access.html",
            {"task": task, "user": user},
            request=request,
        )

    return JsonResponse({'html': html})

@login_required
def delete_task(request, task_id):
    task = get_object_or_404(Task, id=task_id)

    if request.method == 'POST':
        task.is_delete = True
        task.user_delete = request.user
        task.save()
        return redirect('task_list')  # Or wherever you want to go after deletion

    # fallback for GET
    return redirect('task_list')


@login_required
def delete_time_entry(request, entry_id):
    entry = get_object_or_404(TimeEntry, id=entry_id)
    task = entry.task
    # Check if the logged-in user is assigned to the task
    if task.assigned_to != request.user:
        # messages.error(request, "You are not authorized to delete this time entry.")
        # return redirect('task_detail', task_id=task.id)
        return render('error_page.html',{'title':'دسترسی غیر مجاز','text':'شما مجاز به تغییر زمان وظیفه دیگران نیستید'})

    if request.method == 'POST':
        entry.delete()
        return redirect('task_list')

    # fallback for GET (optional)
    return redirect('task_list')





from django.shortcuts import render, redirect
from .models import Story, Sprint

from django.shortcuts import render, get_object_or_404
from .models import Story, Sprint
@csrf_exempt
def assign_stories_to_project(request):
    # Fetch the sprint by ID, if it doesn't exist return 404
    data = request.GET.dict()
    sprint = data.get('sprint_id',None)
    try:
        sprint = int(sprint)
    except:
        sprint = None
    if sprint is None:
        return render('error_page')
   
    sprint = get_object_or_404(Sprint, id=sprint)
    
    # Get all stories for the selected sprint
    stories = Story.objects.filter(sprint=sprint)
    stories.filter(title='nan').delete()
    
    # Get all projects to display in the dropdown
    projects = Project.objects.all()

    if request.method == 'POST':
        # Process each story and assign the selected project
        for story in stories:
            project_id = request.POST.get(f'project_{story.id}')  # Get the selected project for this story
            if project_id:
                project = Project.objects.get(id=project_id)  # Find the selected project
                story.project = project  # Assign the project to the story
                story.save()

        return redirect('success_page')  # Redirect to a success page after saving the assignments



    return render(request, 'assign_stories_to_project.html', {
        'sprint': sprint,
        'stories': stories,
        'projects': projects,
    })


def select_sprint(request):
    sprints = Sprint.objects.all()  # تمام اسپرینت‌ها را می‌گیریم
    return render(request, 'select_sprint.html', {'sprints': sprints})










from django.http import HttpResponse
from django.db.models import Count, Sum, Q, F
from django.db.models.functions import Coalesce
from decimal import Decimal
from openpyxl import Workbook
from django.contrib.auth.models import User


def export_tasks_report_excel(request):
    users = User.objects.annotate(
        total_tasks=Count('task', filter=Q(task__is_delete=False)),
        todo_tasks=Count('task', filter=Q(task__status='todo')),
        doing_tasks=Count('task', filter=Q(task__status='doing')),
        done_tasks=Count('task', filter=Q(task__status='done')),

        total_goal_time=Coalesce(Sum('task__goal_time'), Decimal('0.0')),
        total_spent_time=Coalesce(Sum('timeentry__hours_spent'), Decimal('0.0')),
    ).annotate(
        remaining_time=F('total_goal_time') - F('total_spent_time')
    )

    wb = Workbook()
    ws = wb.active
    ws.title = "Task Report"

    # هدرها
    ws.append([
        "نام کاربر",
        "تعداد کل تسک",
        "Todo",
        "Doing",
        "Done",
        "ساعت هدف",
        "ساعت انجام شده",
        "ساعت باقی‌مانده"
    ])

    # دیتا
    for u in users:
        ws.append([
            u.username,
            u.total_tasks,
            u.todo_tasks,
            u.doing_tasks,
            u.done_tasks,
            float(u.total_goal_time),
            float(u.total_spent_time),
            float(u.remaining_time),
        ])

    response = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = 'attachment; filename=task_report.xlsx'

    wb.save(response)
    return response












# در فایل views.py یا admin.py

from django.http import JsonResponse
from django.contrib.admin.views.decorators import staff_member_required
from django.core.management import call_command
from django.views.decorators.csrf import csrf_exempt
import logging

logger = logging.getLogger(__name__)

@staff_member_required
@csrf_exempt  # اگر می‌خواهید از خارج از admin هم تست کنید
def debug_send_reminder(request):
    """
    اجرای دستی کامند ارسال پیامک برای دیباگ
    """
    # if request.method == 'POST':
    try:
        # اجرای کامند
        call_command('send_reminder_sms')
        
        return JsonResponse({
            'status': 'success',
            'message': 'کامند با موفقیت اجرا شد'
        })
    except Exception as e:
        logger.error(f'Error in debug_send_reminder: {str(e)}')
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)
    # else:
    #     return JsonResponse({
    #         'status': 'info',
    #         'message': 'برای اجرا از متد POST استفاده کنید'
    #     })