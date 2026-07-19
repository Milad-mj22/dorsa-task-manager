from django.shortcuts import render

# Create your views here.
import json
from django.shortcuts import render

# Create your views here.
from django.shortcuts import render
# Create your views here.
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from jalali_date import datetime2jalali

from timeTracker.models import CommentTask, Task, TimeEntry


@login_required
def user_tasks_json(request):
    scope = request.GET.get('scope', '')
    priority = request.GET.get('priority')  # may be None or ''

    # Parse priority safely
    if priority:
        try:
            priority_int = int(priority)
        except ValueError:
            priority_int = None
    else:
        priority_int = None

    if scope == 'all':
        tasks = Task.objects.filter(is_delete=False)
        times = TimeEntry.objects.all()
    else:
        tasks = Task.objects.filter(is_delete=False, assigned_to=request.user)
        times = TimeEntry.objects.filter(user=request.user)

    data = []
    undone_data = []

    # ===== Undone tasks (for the list at bottom) =====
    # ===== Undone tasks (for the list at bottom) =====
    for task in tasks:
        # Apply priority filter to tasks too
        if priority_int is not None and task.priority != priority_int:
            continue

        if task.status in ('doing', 'done'):
            continue
        else:
            undone_data.append({
                'id': task.id,
                'title': task.title,
                'priority': task.priority,
                'status': task.status,
                'due_date': datetime2jalali(task.created_at).strftime('%Y/%m/%d'),
                'buyer': {
                    'id': task.buyer.id,
                    'username': task.buyer.username,
                } if getattr(task, "buyer", None) else None,
                'assigned': {
                    'id': task.assigned_to.id if getattr(task, "assigned_to", None) else None,
                    'username': task.assigned_to.username if getattr(task, "assigned_to", None) else None,
                },
            })


    # Sort undone tasks by due_date (string YYYY/MM/DD works lexicographically)
    undone_data.sort(key=lambda x: x['priority'])

    # ===== Calendar events built from TimeEntry, with colors =====
    # Priority → color map (match front legend)
    PRIORITY_COLORS = {
        1: "#f97373",  # priority 1 – red
        2: "#facc15",  # priority 2 – yellow
        3: "#4ade80",  # priority 3 – green
    }
    DEFAULT_COLOR = "#38bdf8"  # fallback

    data = []

    # select_related to avoid extra queries
    for time in times.select_related("task"):
        task = time.task
        if task.is_delete:
            continue

        # Apply priority filter on time-based events too
        if priority_int is not None and task.priority != priority_int:
            continue

        color = PRIORITY_COLORS.get(task.priority, DEFAULT_COLOR)

        task_data = {
            'id': task.id,
            'title': task.title,
            'is_done': task.status,  # you can keep your string status here

            'start': time.datetime.strftime('%Y-%m-%d'),
            'start_jalalian': datetime2jalali(time.datetime).strftime('%Y/%m/%d'),
            'color': color,
            'allDay': True,
        }
        data.append(task_data)

    return JsonResponse({
        'tasks': data,
        'undone_tasks': undone_data
    })


@login_required
def calendar_view(request):
    return render(request, 'tasks/dashboard_calendar.html')









@csrf_exempt
def update_task(request, task_id):
    if request.method == 'POST':
        task = Task.objects.get(id=task_id, assigned_to=request.user)
        data = json.loads(request.body)

        task.is_done = data.get('done', False)
        task.save()

        comment = data.get('comment', '')
        if comment !='':
            CommentTask.objects.create(task_id=task,description=comment,created_by=request.user)
     

        return JsonResponse({'success': True})
    return JsonResponse({'success': False}, status=400)

