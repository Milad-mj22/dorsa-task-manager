from django.shortcuts import render

# Create your views here.
# views.py
from decimal import Decimal
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db.models import Sum, Value , Q
from django.db.models.functions import Coalesce
from django.shortcuts import get_object_or_404, render

from .models import Project
from timeTracker.models import Sprint, Story, Task, TimeEntry  # adjust import paths to your app
from django.db.models import Sum, Value, DecimalField
DECIMAL = DecimalField(max_digits=12, decimal_places=2)
@login_required
def project_time_report(request, project_id):
    project = get_object_or_404(Project, id=project_id)

    # ✅ sprints available for this project (through stories)
    sprints_qs = Sprint.objects.filter(
        story__project=project
    ).distinct().order_by("-start_date", "-id")

    last_sprint = sprints_qs.first()
    selected_sprint = request.GET.get("sprint")

    # default: last sprint (if exists)
    if not selected_sprint and last_sprint:
        selected_sprint = str(last_sprint.id)

    sprint_filter_id = None
    if selected_sprint and selected_sprint != "all":
        try:
            sprint_filter_id = int(selected_sprint)
        except (TypeError, ValueError):
            sprint_filter_id = None

    # ✅ base queryset for time entries in this project
    time_qs = TimeEntry.objects.filter(
        task__story__project=project
    )

    # ✅ apply sprint filter if not "all"
    if sprint_filter_id:
        time_qs = time_qs.filter(task__story__sprint_id=sprint_filter_id)

    # ----------------------------
    # Totals
    # ----------------------------
    total_spent = time_qs.aggregate(
        total=Coalesce(Sum("hours_spent"), Value(0), output_field=DECIMAL)
    )["total"] or 0

    # ----------------------------
    # Per-user totals
    # ----------------------------
    per_user = (
        time_qs.values("user_id", "user__username")
        .annotate(spent=Coalesce(Sum("hours_spent"), Value(0), output_field=DECIMAL))
        .order_by("-spent", "user__username")
    )

    # Optional: limit to project.persons users (if you want to hide others)
    # per_user = per_user.filter(user__in=project.persons.all())  # NOTE: requires join style change if needed

    # selected sprint obj for UI label
    selected_sprint_obj = None
    if sprint_filter_id:
        selected_sprint_obj = sprints_qs.filter(id=sprint_filter_id).first()

    return render(request, "projects/project_time_report.html", {
        "project": project,
        "sprints": sprints_qs,
        "selected_sprint": selected_sprint or "all",
        "selected_sprint_obj": selected_sprint_obj,
        "total_spent": total_spent,
        "per_user": per_user,
    })


@login_required
def projects_time_summary(request):
    # Sprint dropdown options
    sprints_qs = Sprint.objects.all().order_by("-start_date", "-id")

    last_sprint = sprints_qs.first()
    selected_sprint = request.GET.get("sprint")

    # default: last sprint (optional behavior; comment out if you want default=all)
    if not selected_sprint and last_sprint:
        selected_sprint = str(last_sprint.id)

    sprint_filter_id = None
    if selected_sprint and selected_sprint != "all":
        try:
            sprint_filter_id = int(selected_sprint)
        except (TypeError, ValueError):
            sprint_filter_id = None

    # selected sprint object for label
    selected_sprint_obj = None
    if sprint_filter_id:
        selected_sprint_obj = sprints_qs.filter(id=sprint_filter_id).first()

    # ---------------------------------------------------------
    # Projects queryset + conditional aggregation for spent time
    # ---------------------------------------------------------
    projects_qs = Project.objects.select_related("city").prefetch_related("persons")

    if sprint_filter_id:
        projects_qs = projects_qs.annotate(
            total_spent=Coalesce(
                Sum(
                    "story__task__timeentry__hours_spent",
                    filter=Q(story__sprint_id=sprint_filter_id),
                ),
                Value(Decimal("0.00")),
                output_field=DECIMAL,
            )
        )
    else:
        projects_qs = projects_qs.annotate(
            total_spent=Coalesce(
                Sum("story__task__timeentry__hours_spent"),
                Value(Decimal("0.00")),
                output_field=DECIMAL,
            )
        )

    rows = projects_qs.order_by("-total_spent", "name")

    # ---------------------------------------------------------
    # Grand total (optional)
    # ---------------------------------------------------------
    time_qs = TimeEntry.objects.filter(task__story__project__isnull=False)
    if sprint_filter_id:
        time_qs = time_qs.filter(task__story__sprint_id=sprint_filter_id)

    grand_total = time_qs.aggregate(
        total=Coalesce(Sum("hours_spent"), Value(Decimal("0.00")), output_field=DECIMAL)
    )["total"] or Decimal("0.00")

    # ---------------------------------------------------------
    # ✅ Mini-chart data: per-project per-user hours (contributors)
    # ---------------------------------------------------------
    contrib_qs = TimeEntry.objects.filter(task__story__project__isnull=False)
    if sprint_filter_id:
        contrib_qs = contrib_qs.filter(task__story__sprint_id=sprint_filter_id)

    total_time = 0
    
    if sprint_filter_id:
        total_time = Sprint.objects.filter(id=sprint_filter_id).first().total_hours
    else:
        total_sprints = Sprint.objects.all()

        for sprint in total_sprints:
            total_time += sprint.total_hours

    active_users_count = TimeEntry.objects.filter(task__story__project__isnull=False)
    if sprint_filter_id:
        active_users_count = active_users_count.filter(task__story__sprint_id=sprint_filter_id)
    active_users_count = active_users_count.values("user_id").distinct().count()
    
    avg_per_user = Decimal("0.00")
    if active_users_count > 0:
        avg_per_user = (grand_total / Decimal(active_users_count)).quantize(Decimal("0.01"))
   
   
    user_contrib_rows = (
        time_qs.values("user_id", "user__username")
        .annotate(total=Coalesce(Sum("hours_spent"), Value(Decimal("0.00")), output_field=DECIMAL))
        .order_by("-total", "user__username")
    )

    user_contrib = []
    for r in user_contrib_rows:
        pct = Decimal("0.0")
        if grand_total > 0:
            pct = (r["total"] / grand_total * 100).quantize(Decimal("0.1"))
        user_contrib.append({
            "username": r["user__username"],
            "hours": r["total"],
            "pct": pct,
        })

    total_time = total_time * 8
    
   
    contrib_rows = (
        contrib_qs.values(
            "task__story__project_id",
            "user_id",
            "user__username",
        )
        .annotate(spent=Coalesce(Sum("hours_spent"), Value(Decimal("0.00")), output_field=DECIMAL))
        .order_by("task__story__project_id", "-spent", "user__username")
    )

    contributors_by_project = {}
    for x in contrib_rows:
        pid = x["task__story__project_id"]
        contributors_by_project.setdefault(pid, []).append({
            "username": x["user__username"],
            "spent": x["spent"],
        })

    # compute max per project for bar scaling
    for pid, lst in contributors_by_project.items():
        max_spent = max((c["spent"] for c in lst), default=Decimal("0.00"))
        contributors_by_project[pid] = {
            "max_spent": max_spent,
            "items": lst[:6],  # ✅ show top 6 in mini chart (adjust as you like)
            "more_count": max(0, len(lst) - 6),
        }

    return render(request, "projects/projects_time_summary.html", {
        "rows": rows,
        "sprints": sprints_qs,
        "selected_sprint": selected_sprint or "all",
        "selected_sprint_obj": selected_sprint_obj,
        "grand_total": grand_total,

        # ✅ mini chart
        "contributors_by_project": contributors_by_project,
        "grand_total": grand_total,
        "active_users_count": active_users_count,
        "avg_per_user": avg_per_user,
        "user_contrib": user_contrib,   # optional for showing top contributors
        "total_time":total_time    
    
    })