
from django.shortcuts import render
from django.db.models import Sum
from django.shortcuts import render
import jdatetime
from timeTracker.models import TimeEntry, Sprint, Team, User,Task


from django.db.models.functions import TruncDate
from collections import defaultdict
import json
# Create your views here.

def team_dashboard(request):

    from collections import defaultdict
    from django.db.models import Sum



    team_task_data = defaultdict(list)

    entries = TimeEntry.objects.select_related('task__story__team').all()

    for entry in entries:
        team_name = entry.task.story.team.name
        task_title = entry.task.title
        team_task_data[team_name].append((task_title, float(entry.hours_spent)))

    # Aggregate data by task title for each team
    final_team_data = {}
    for team, task_entries in team_task_data.items():
        agg = {}
        for title, hours in task_entries:
            agg[title] = agg.get(title, 0) + hours
        final_team_data[team] = agg

    return render(request, 'data_dashboard.html', {
        'final_team_data': final_team_data,
    })




def selective_dashboard(request):

    from collections import defaultdict
    from django.db.models import Sum

    import json
    sprint_id = request.GET.get('sprint')
    sprints = Sprint.objects.all()
    selected_sprint = Sprint.objects.filter(id=sprint_id).first() if sprint_id else sprints.first()

    entries = TimeEntry.objects.select_related('task__story__team', 'user', 'task__story__sprint')
    if selected_sprint:
        entries = entries.filter(task__story__sprint=selected_sprint)

    # Structure: {team: {task: {user: hours}}}
    stacked_data = defaultdict(lambda: defaultdict(lambda: defaultdict(float)))
    goal_data = defaultdict(lambda: {})

    for entry in entries:
        team = entry.task.story.team.name
        task = entry.task.title
        user = entry.user.username
        stacked_data[team][task][user] += float(entry.hours_spent)
        goal_data[team][task] = float(entry.task.goal_time)

    # Convert nested defaultdicts to normal dicts for safe use in template/JS
    stacked_data_json = json.dumps(stacked_data)
    goal_data_json = json.dumps(goal_data)

    return render(request, 'selective_dashboard.html', {
        'sprints': sprints,
        'selected_sprint': selected_sprint,
        'stacked_data_json': stacked_data_json,
        'goal_data_json': goal_data_json,
    })



def data_dashboard_view(request):
    from collections import defaultdict
    import json

    sprint_id = request.GET.get('sprint')
    sprints = Sprint.objects.all()
    sprints_qs = Sprint.objects.filter( is_active=True).distinct()

    if sprint_id is None:
        selected_sprint = sprints_qs.order_by('-start_date', '-id').first()
    else:
        selected_sprint = Sprint.objects.filter(id=sprint_id).first() 

    entries = TimeEntry.objects.select_related('task__story__team', 'user', 'task__story__sprint')
    if selected_sprint:
        entries = entries.filter(task__story__sprint=selected_sprint)

    # Structure: {team: {task: {user: hours}}}
    stacked_data = defaultdict(lambda: defaultdict(lambda: defaultdict(float)))
    goal_data = defaultdict(dict)

    for entry in entries:
        team = entry.task.story.team.name
        task = entry.task.title
        user = entry.user.username
        stacked_data[team][task][user] += float(entry.hours_spent)
        goal_data[team][task] = float(entry.task.goal_time)

    # Total hours per team
    team_total_hours = (
        entries
        .values('task__story__team__name')
        .annotate(total_hours=Sum('hours_spent'))
        .order_by('-total_hours')
    )

    # Prepare for chart (labels and values)
    team_hours_chart = {
        "labels": [entry['task__story__team__name'] for entry in team_total_hours],
        "values": [float(entry['total_hours']) for entry in team_total_hours],
    }

    # Convert to normal dicts
    def convert(d):
        if isinstance(d, defaultdict):
            d = {k: convert(v) for k, v in d.items()}
        return d

    stacked_data_json = json.dumps(convert(stacked_data))
    goal_data_json = json.dumps(convert(goal_data))

    return render(request, 'data_dashboard.html', {
        'sprints': sprints,
        'selected_sprint': selected_sprint,
        'stacked_data_json': stacked_data_json,
        'goal_data_json': goal_data_json,
        'team_hours_chart': json.dumps(team_hours_chart),
    })





def team_overview_view(request):
    import json
    # Get all teams
    teams = Team.objects.all()

    # Prepare structure: {team_name: {users: [{name, time}], total: total_time}}
    overview_data = {}

    for team in teams:
        user_times = (
            TimeEntry.objects
            .filter(task__story__team=team,task__story__sprint__is_active=True)
            .values('user__username')
            .annotate(total=Sum('hours_spent'))
            .order_by('-total')
        )

        overview_data[team.name] = {
            'users': [
                {'name': u['user__username'], 'time': float(u['total'])}
                for u in user_times
            ],
            'total': sum(float(u['total']) for u in user_times)
        }

    return render(request, 'team_overview.html', {
        'overview_data': overview_data,
        'overview_json': json.dumps(overview_data),
    })




def team_timeline_view(request):
    entries = TimeEntry.objects.select_related('task__story__team', 'user').order_by('datetime')

    # Structure: {team: {date: hours}}
    timeline_data = defaultdict(lambda: defaultdict(float))
    all_dates = set()

    for entry in entries:
        team = entry.task.story.team.name
        day = entry.datetime.isoformat()
        timeline_data[team][day] += float(entry.hours_spent)
        all_dates.add(day)

    sorted_dates = sorted(all_dates)

    # Prepare chart format
    chart_data = {
        "labels": sorted_dates,
        "datasets": []
    }

    for i, (team, team_values) in enumerate(timeline_data.items()):
        chart_data["datasets"].append({
            "label": team,
            "data": [team_values.get(day, 0) for day in sorted_dates],
            "fill": False,
            "borderColor": f"hsl({i * 45 % 360}, 70%, 50%)",
            "tension": 0.3
        })

    return render(request, 'team_timeline.html', {
        'chart_json': json.dumps(chart_data)
    })





from decimal import Decimal
from django.contrib.auth.models import User
from django.db.models import Sum, F, Value, DecimalField
from django.db.models.functions import Coalesce, Greatest
from django.shortcuts import render



DECIMAL = DecimalField(max_digits=12, decimal_places=2)


def _clamp_decimal(x: Decimal, lo: Decimal, hi: Decimal) -> Decimal:
    if x < lo:
        return lo
    if x > hi:
        return hi
    return x

from decimal import Decimal
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db.models import Sum, Value, F
from django.db.models.functions import Coalesce, Greatest
from django.shortcuts import render

@login_required
def users_task_dashboard(request):
    excluded_usernames = ["test", "test2", "milad_test", "milad"]
    users = User.objects.exclude(username__in=excluded_usernames)

    # ✅ sprints for dropdown (adjust team filtering if you want)
    sprints_qs = Sprint.objects.filter(is_active=True).order_by("-start_date", "-id")
    last_sprint = sprints_qs.first()

    selected_sprint = request.GET.get("sprint")  # can be None, "all", or an id string

    # ✅ default behavior: if not provided => last sprint
    if not selected_sprint and last_sprint:
        selected_sprint = str(last_sprint.id)

    # ✅ interpret selection
    sprint_filter_id = None
    if selected_sprint and selected_sprint != "all":
        try:
            sprint_filter_id = int(selected_sprint)
        except (TypeError, ValueError):
            sprint_filter_id = None  # fallback to "no filter"

    rows = []

    for user in users:
        base_tasks = Task.objects.filter(
            assigned_to=user,
            is_delete=False
        )

        # ✅ apply sprint filter (ONLY if not "all")
        # Change this path if your FK differs:
        # e.g. base_tasks = base_tasks.filter(sprint_id=sprint_filter_id)
        if sprint_filter_id:
            base_tasks = base_tasks.filter(story__sprint_id=sprint_filter_id)

        base_tasks = base_tasks.annotate(
            spent=Coalesce(Sum("timeentry__hours_spent"), Value(0), output_field=DECIMAL),
        ).annotate(
            remaining=Greatest(
                Coalesce(F("goal_time"), Value(0), output_field=DECIMAL) - F("spent"),
                Value(0),
                output_field=DECIMAL
            )
        )

        todo_tasks = base_tasks.filter(status="todo")
        doing_tasks = base_tasks.filter(status="doing")
        done_tasks = base_tasks.filter(status="done")

        all_tasks_agg = base_tasks.aggregate(
            total_goal=Coalesce(Sum("goal_time"), Value(0), output_field=DECIMAL),
            total_spent=Coalesce(Sum("spent"), Value(0), output_field=DECIMAL),
            total_remaining=Coalesce(Sum("remaining"), Value(0), output_field=DECIMAL),
        )

        total_goal_all = all_tasks_agg["total_goal"] or Decimal("0")
        total_spent_all_tasks = all_tasks_agg["total_spent"] or Decimal("0")
        total_remaining_all = all_tasks_agg["total_remaining"] or Decimal("0")

        if total_goal_all > 0:
            progress_raw = (total_spent_all_tasks / total_goal_all) * 100
        else:
            progress_raw = Decimal("0")

        progress_ui = _clamp_decimal(progress_raw, Decimal("0"), Decimal("100"))
        progress_int = int(progress_ui.quantize(Decimal("1")))
        progress_display = progress_ui.quantize(Decimal("0.1"))

        is_overrun = (total_goal_all > 0 and total_spent_all_tasks > total_goal_all)
        overrun_percent = progress_raw.quantize(Decimal("0.1")) if total_goal_all > 0 else Decimal("0.0")

        is_overcommit = (
            total_goal_all >= Decimal("20")
            and progress_ui < Decimal("40")
            and total_remaining_all >= Decimal("10")
        )

        if progress_ui >= Decimal("70"):
            status_text, status_class, progress_class = "✅ عملکرد خوب", "pill-good", "p-good"
        elif progress_ui >= Decimal("40"):
            status_text, status_class, progress_class = "⚠️ عملکرد متوسط", "pill-mid", "p-mid"
        else:
            status_text, status_class, progress_class = "⛔ عملکرد ضعیف", "pill-low", "p-low"

        done_agg = done_tasks.aggregate(
            done_goal=Coalesce(Sum("goal_time"), Value(0), output_field=DECIMAL),
            done_spent=Coalesce(Sum("spent"), Value(0), output_field=DECIMAL),
            done_remaining=Coalesce(Sum("remaining"), Value(0), output_field=DECIMAL),
        )

        rows.append({
            "user": user,
            "total_goal_all": total_goal_all,
            "total_spent_all_tasks": total_spent_all_tasks,
            "total_remaining_all": total_remaining_all,

            "progress_int": progress_int,
            "progress_display": progress_display,
            "progress_raw_display": overrun_percent,
            "status_text": status_text,
            "status_class": status_class,
            "progress_class": progress_class,

            "is_overrun": is_overrun,
            "is_overcommit": is_overcommit,

            "todo_tasks": todo_tasks,
            "doing_tasks": doing_tasks,
            "done_tasks": done_tasks,

            "done_total_goal": done_agg["done_goal"],
            "done_total_spent": done_agg["done_spent"],
            "done_total_remaining": done_agg["done_remaining"],
        })

    rows_sorted = sorted(
        rows,
        key=lambda r: (Decimal(r["progress_display"]), Decimal(r["total_spent_all_tasks"])),
        reverse=True
    )

    for idx, r in enumerate(rows_sorted, start=1):
        r["rank"] = idx
        r["rank_badge"] = "🥇" if idx == 1 else "🥈" if idx == 2 else "🥉" if idx == 3 else "⭐"

    summary = {"users_count": len(rows_sorted)}

    return render(
        request,
        "scrum_reports/sprint_hours.html",
        {
            "data": rows_sorted,
            "summary": summary,
            "sprints": sprints_qs,                 # ✅ for dropdown
            "selected_sprint": selected_sprint,    # ✅ "all" or id as string
        }
    )






















from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from datetime import datetime, timedelta
from django.db.models import Sum, Q
from django.http import HttpResponse
import csv
import openpyxl
from openpyxl.styles import Font, Alignment, PatternFill
from timeTracker.models import TimeEntry, Task, Story, Team, Sprint
from Projects.models import Project  # Adjust import based on your structure


@login_required
def daily_work_report(request):
    # Get date parameter, default to today
    selected_date = request.GET.get('date')
    if selected_date:
        try:
            selected_date = datetime.strptime(selected_date, '%Y-%m-%d').date()
        except ValueError:
            selected_date = timezone.now().date()
    else:
        selected_date = timezone.now().date()
    
    # Get last 30 days including selected date (changed from 20 to 30)
    last_30_days = []
    for i in range(29, -1, -1):
        day = selected_date + timedelta(days=7)  - timedelta(days=i) 
        
        # Check if there are entries for this day
        has_data = TimeEntry.objects.filter(datetime__date=day).exists()
        total_hours_for_day = TimeEntry.objects.filter(
            datetime__date=day
        ).aggregate(Sum('hours_spent'))['hours_spent__sum'] or 0
        
        # Convert to Jalali
        try:
            jalali_date = jdatetime.date.fromgregorian(date=day)
            jalali_day = jalali_date.day
            # Persian month abbreviations
            persian_months = ['فروردین', 'اردیبهشت', 'خرداد', 'تیر', 'مرداد', 'شهریور', 'مهر', 'آبان', 'آذر', 'دی', 'بهمن', 'اسفند']
            jalali_month_short = persian_months[jalali_date.month - 1]
            jalali_full = jalali_date.strftime('%d %B %Y')
        except Exception as e:
            # Fallback to Gregorian if jdatetime fails
            jalali_day = day.day
            jalali_month_short = day.strftime('%b')
            jalali_full = day.strftime('%d %B %Y')
        
        last_30_days.append({
            'gregorian': day,
            'jalali_full': jalali_full,
            'jalali_day': jalali_day,
            'jalali_month_short': jalali_month_short,
            'is_selected': day == selected_date,
            'has_data': has_data,
            'total_hours': total_hours_for_day
        })
    
    # Get time entries for the selected date
    time_entries = TimeEntry.objects.filter(
        datetime__date=selected_date
    ).select_related(
        'task',
        'task__story',
        'task__story__project',
        'task__story__team',
        'task__story__sprint',
        'user'
    ).order_by('user__username', 'task__story__project__name', 'task__wbs_row')
    
    # Organize data by user, then by project, then by task
    report_data = {}
    total_hours = 0
    total_tasks = set()  # For counting unique tasks
    
    for entry in time_entries:
        user = entry.user
        task = entry.task
        story = task.story
        project = story.project
        wbs_row = task.wbs_row or 'N/A'
        
        # Track unique tasks
        total_tasks.add(task.id)
        
        # Initialize user dict
        if user not in report_data:
            report_data[user] = {
                'projects': {},
                'total_user_hours': 0,
                'user_full_name': user.get_full_name() or user.username
            }
        
        # Initialize project dict
        project_name = project.name if project else 'بدون پروژه'
        if project_name not in report_data[user]['projects']:
            report_data[user]['projects'][project_name] = {
                'tasks': {},
                'project_total': 0,
                'wbs_rows': set()
            }
        
        # Initialize task dict
        task_key = f"{task.id}_{task.title}"
        if task_key not in report_data[user]['projects'][project_name]['tasks']:
            report_data[user]['projects'][project_name]['tasks'][task_key] = {
                'task': task,
                'hours': 0,
                'wbs_row': wbs_row,
                'story_title': story.title if story else 'بدون داستان',
                'priority': task.priority
            }
        
        # Add hours
        report_data[user]['projects'][project_name]['tasks'][task_key]['hours'] += entry.hours_spent
        report_data[user]['projects'][project_name]['project_total'] += entry.hours_spent
        report_data[user]['total_user_hours'] += entry.hours_spent
        report_data[user]['projects'][project_name]['wbs_rows'].add(wbs_row)
        total_hours += entry.hours_spent
    
    # Convert sets to lists for template
    for user, data in report_data.items():
        for project, project_data in data['projects'].items():
            project_data['wbs_rows'] = list(project_data['wbs_rows'])
    
    # Convert selected date to Jalali for display
    try:
        jalali_selected = jdatetime.date.fromgregorian(date=selected_date)
        selected_date_jalali = jalali_selected.strftime('%d %B %Y')
        selected_date_jalali_short = jalali_selected.strftime('%d %B')
    except:
        selected_date_jalali = selected_date.strftime('%d %B %Y')
        selected_date_jalali_short = selected_date.strftime('%d %b')
    
    context = {
        'report_data': report_data,
        'selected_date': selected_date,
        'selected_date_jalali': selected_date_jalali,
        'selected_date_jalali_short': selected_date_jalali_short,
        'last_30_days': last_30_days,
        'total_hours': total_hours,
        'total_users': len(report_data),
        'total_tasks': len(total_tasks),
        'today': timezone.now().date(),
    }
    
    return render(request, 't1.html', context)
@login_required
def export_daily_report_csv(request):
    """Export daily report as CSV with Jalali date"""
    selected_date = request.GET.get('date')
    if selected_date:
        try:
            selected_date = datetime.strptime(selected_date, '%Y-%m-%d').date()
        except ValueError:
            selected_date = timezone.now().date()
    else:
        selected_date = timezone.now().date()
    
    # Get Jalali date for filename
    try:
        jalali_date = jdatetime.date.fromgregorian(date=selected_date)
        date_str = jalali_date.strftime('%Y-%m-%d')
    except:
        date_str = selected_date.strftime('%Y-%m-%d')
    
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="daily_work_report_{date_str}.csv"'
    
    writer = csv.writer(response)
    writer.writerow([
        'User', 'Project', 'WBS Row', 'Task', 'Story', 
        'Team', 'Sprint', 'Hours Spent', 'Date (Gregorian)', 'Date (Jalali)'
    ])
    
    time_entries = TimeEntry.objects.filter(
        datetime__date=selected_date
    ).select_related(
        'task',
        'task__story',
        'task__story__project',
        'task__story__team',
        'task__story__sprint',
        'user'
    ).order_by('user__username', 'task__story__project__name')
    
    for entry in time_entries:
        # Get Jalali date
        try:
            jalali_entry = jdatetime.date.fromgregorian(date=entry.datetime.date())
            jalali_str = jalali_entry.strftime('%Y/%m/%d')
        except:
            jalali_str = entry.datetime.date().strftime('%Y-%m-%d')
        
        writer.writerow([
            entry.user.username,
            entry.task.story.project.name if entry.task.story.project else 'No Project',
            entry.task.wbs_row or 'N/A',
            entry.task.title,
            entry.task.story.title,
            entry.task.story.team.name if entry.task.story.team else 'No Team',
            entry.task.story.sprint.name if entry.task.story.sprint else 'No Sprint',
            str(entry.hours_spent),
            entry.datetime.date(),
            jalali_str
        ])
    
    return response


@login_required
def export_daily_report_excel(request):
    """Export daily report as Excel with Jalali date"""
    selected_date = request.GET.get('date')
    if selected_date:
        try:
            selected_date = datetime.strptime(selected_date, '%Y-%m-%d').date()
        except ValueError:
            selected_date = timezone.now().date()
    else:
        selected_date = timezone.now().date()
    
    # Get Jalali date for filename
    try:
        jalali_date = jdatetime.date.fromgregorian(date=selected_date)
        date_str = jalali_date.strftime('%Y-%m-%d')
    except:
        date_str = selected_date.strftime('%Y-%m-%d')
    
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = 'Daily Report'
    
    headers = [
        'User', 'Project', 'WBS Row', 'Task', 'Story', 
        'Team', 'Sprint', 'Hours Spent', 'Date (Gregorian)', 'Date (Jalali)'
    ]
    
    # Style headers
    header_font = Font(bold=True, color='FFFFFF')
    header_fill = PatternFill(start_color='4F81BD', end_color='4F81BD', fill_type='solid')
    header_alignment = Alignment(horizontal='center', vertical='center')
    
    for col, header in enumerate(headers, 1):
        cell = ws.cell(row=1, column=col, value=header)
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = header_alignment
    
    time_entries = TimeEntry.objects.filter(
        datetime__date=selected_date
    ).select_related(
        'task',
        'task__story',
        'task__story__project',
        'task__story__team',
        'task__story__sprint',
        'user'
    ).order_by('user__username', 'task__story__project__name')
    
    row_num = 2
    for entry in time_entries:
        # Get Jalali date
        try:
            jalali_entry = jdatetime.date.fromgregorian(date=entry.datetime.date())
            jalali_str = jalali_entry.strftime('%Y/%m/%d')
        except:
            jalali_str = entry.datetime.date().strftime('%Y-%m-%d')
        
        ws.cell(row=row_num, column=1, value=entry.user.username)
        ws.cell(row=row_num, column=2, value=entry.task.story.project.name if entry.task.story.project else 'No Project')
        ws.cell(row=row_num, column=3, value=entry.task.wbs_row or 'N/A')
        ws.cell(row=row_num, column=4, value=entry.task.title)
        ws.cell(row=row_num, column=5, value=entry.task.story.title)
        ws.cell(row=row_num, column=6, value=entry.task.story.team.name if entry.task.story.team else 'No Team')
        ws.cell(row=row_num, column=7, value=entry.task.story.sprint.name if entry.task.story.sprint else 'No Sprint')
        ws.cell(row=row_num, column=8, value=float(entry.hours_spent))
        ws.cell(row=row_num, column=9, value=str(entry.datetime.date()))
        ws.cell(row=row_num, column=10, value=jalali_str)
        row_num += 1
    
    # Auto-adjust column widths
    for column in ws.columns:
        max_length = 0
        column_letter = column[0].column_letter
        for cell in column:
            try:
                if len(str(cell.value)) > max_length:
                    max_length = len(str(cell.value))
            except:
                pass
        adjusted_width = min(max_length + 2, 50)
        ws.column_dimensions[column_letter].width = adjusted_width
    
    response = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = f'attachment; filename="daily_work_report_{date_str}.xlsx"'
    wb.save(response)
    
    return response

@login_required
def export_daily_report_excel(request):
    """Export daily report as Excel"""
    selected_date = request.GET.get('date')
    if selected_date:
        try:
            selected_date = datetime.strptime(selected_date, '%Y-%m-%d').date()
        except ValueError:
            selected_date = timezone.now().date()
    else:
        selected_date = timezone.now().date()
    
    # Create Excel workbook
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = 'Daily Report'
    
    # Headers
    headers = [
        'User', 'Project', 'WBS Row', 'Task', 'Story', 
        'Team', 'Sprint', 'Hours Spent', 'Date'
    ]
    
    # Style headers
    header_font = Font(bold=True, color='FFFFFF')
    header_fill = PatternFill(start_color='4F81BD', end_color='4F81BD', fill_type='solid')
    header_alignment = Alignment(horizontal='center', vertical='center')
    
    for col, header in enumerate(headers, 1):
        cell = ws.cell(row=1, column=col, value=header)
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = header_alignment
    
    # Get data
    time_entries = TimeEntry.objects.filter(
        datetime__date=selected_date
    ).select_related(
        'task',
        'task__story',
        'task__story__project',
        'task__story__team',
        'task__story__sprint',
        'user'
    ).order_by('user__username', 'task__story__project__name')
    
    row_num = 2
    for entry in time_entries:
        ws.cell(row=row_num, column=1, value=entry.user.username)
        ws.cell(row=row_num, column=2, value=entry.task.story.project.name if entry.task.story.project else 'No Project')
        ws.cell(row=row_num, column=3, value=entry.task.wbs_row or 'N/A')
        ws.cell(row=row_num, column=4, value=entry.task.title)
        ws.cell(row=row_num, column=5, value=entry.task.story.title)
        ws.cell(row=row_num, column=6, value=entry.task.story.team.name if entry.task.story.team else 'No Team')
        ws.cell(row=row_num, column=7, value=entry.task.story.sprint.name if entry.task.story.sprint else 'No Sprint')
        ws.cell(row=row_num, column=8, value=float(entry.hours_spent))
        ws.cell(row=row_num, column=9, value=str(entry.datetime.date()))
        row_num += 1
    
    # Auto-adjust column widths
    for column in ws.columns:
        max_length = 0
        column_letter = column[0].column_letter
        for cell in column:
            try:
                if len(str(cell.value)) > max_length:
                    max_length = len(str(cell.value))
            except:
                pass
        adjusted_width = min(max_length + 2, 50)
        ws.column_dimensions[column_letter].width = adjusted_width
    
    # Create response
    response = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = f'attachment; filename="daily_work_report_{selected_date}.xlsx"'
    wb.save(response)
    
    return response