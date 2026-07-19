from django.http import JsonResponse
from django.shortcuts import render , get_object_or_404 , redirect
from django.contrib.auth.decorators import login_required

from Missions.models import Mission, MissionApproval, MissionFlow
from Missions.utils import convert_jalali_to_gregorian
# Create your views here.
from .forms import MissionCommentForm, MissionForm

from django.db.models import Sum, Count, Q, F




@login_required
def mission_create(request):
    if request.method == "POST":
        form = MissionForm(request.POST)
        if form.is_valid():
            start_date = request.POST.get('start_date','')
            if start_date !='':
                start_date = convert_jalali_to_gregorian(start_date)
            end_date = request.POST.get('end_date','')
            if end_date != '':
                end_date = convert_jalali_to_gregorian(end_date)
            price = request.POST.get('attr_price','')

            request.POST

            mission = form.save(commit=False)
            
            mission.created_by = request.user
            if start_date!='':
                mission.start_date = start_date
            if end_date!='':
                mission.end_date = end_date
            if price!='':
                mission.price = float(price.replace(',', ''))

            # mission.bootstrap_flow_from_type
            mission.save()
            form.save_m2m()  # Save many-to-many persons
            mission.bootstrap_flow_from_type()
            return redirect("mission_list")
    else:
        form = MissionForm()

    return render(request, "missions/mission_create.html", {"form": form})



@login_required
def mission_flow_list(request, mission_id):
    """Show all flow steps for a mission, with approval statuses."""
    mission = get_object_or_404(Mission, id=mission_id)
    flows = mission.flows.prefetch_related('approvers', 'approvals__user').all()

    context = {
        "mission": mission,
        "flows": flows,
        "user": request.user,
    }
    return render(request, "missions/mission_flow_list.html", context)


@login_required
def approve_step(request, flow_id):
    """Approve a specific flow step for the current user (toggle)."""
    flow = get_object_or_404(MissionFlow, id=flow_id)
    user = request.user

    # Check if user is an approver for this step
    if user not in flow.approvers.all():
        return JsonResponse({"success": False, "message": "شما اجازه تایید این مرحله را ندارید."})

    approval, created = MissionApproval.objects.get_or_create(flow=flow, user=user)
    approval.approved = True
    approval.save()

    # Check if all approvers have approved
    flow.check_approval_status()

    return JsonResponse({
        "success": True,
        "approved": approval.approved,
        "flow_approved": flow.approved,
    })





@login_required
def mission_list(request):
    missions = Mission.objects.filter(
        Q(created_by=request.user) | Q(persons=request.user)
    ).distinct()
    return render(request, 'missions/mission_list.html', {'missions': missions})


from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, render, redirect
from django.db.models import Prefetch

from .models import Mission, MissionFlow, MissionApproval
from .forms import MissionCommentForm


@login_required
def mission_detail(request, pk):
    # Eager load related data
    mission_qs = (
        Mission.objects
        .select_related('project', 'created_by', 'type')
        .prefetch_related(
            'persons',
            Prefetch(
                'flows',
                queryset=MissionFlow.objects
                    .order_by('position')
                    .prefetch_related(
                        'approvers',
                        Prefetch(
                            'approvals',
                            queryset=MissionApproval.objects.select_related('user')
                        )
                    ),
                to_attr='prefetched_flows'  # attach as mission.prefetched_flows
            ),
            Prefetch('comments', to_attr='prefetched_comments')  # author is selected later
        )
    )
    mission = get_object_or_404(mission_qs, pk=pk)

    # Ensure user is involved (creator or in persons)
    is_involved = (
        request.user == mission.created_by
        or mission.persons.filter(pk=request.user.pk).exists()
    )
    if not is_involved:
        return redirect('mission_list')

    # Optional: auto-bootstrap flow if type is set and no steps exist yet
    # if mission.type and not mission.flows.exists():
    #     mission.bootstrap_flow_from_type()
    #     mission.refresh_from_db()

    # Comments (attach authors efficiently)
    comments = (
        mission.comments.select_related('author').all()
        if not hasattr(mission, 'prefetched_comments')
        else [c for c in mission.prefetched_comments]  # already prefetched (without author)
    )

    # Flows for template
    flows = (
        mission.flows.order_by('position')
        if not hasattr(mission, 'prefetched_flows')
        else mission.prefetched_flows
    )

    if request.method == 'POST':
        form = MissionCommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.mission = mission
            comment.author = request.user
            comment.save()
            return redirect('mission_detail', pk=mission.pk)
    else:
        form = MissionCommentForm()

    return render(request, 'missions/mission_detail.html', {
        'mission': mission,
        'flows': flows,
        'comments': comments,
        'form': form,
        'progress_percent': mission.progress_percent,  # if you want to use the progress bar
    })





from django.db.models import Exists, OuterRef
from django.views.decorators.http import require_POST

@login_required
def my_pending_approvals(request):
    # Current steps where I am an approver and I haven't approved yet
    flows_qs = (
        MissionFlow.objects
        .filter(is_current=True, approvers=request.user)
        .annotate(
            i_approved=Exists(
                MissionApproval.objects.filter(
                    flow=OuterRef('pk'),
                    user=request.user,
                    approved=True,
                )
            )
        )
        .filter(i_approved=False)
        .select_related('mission', 'mission__project')
        .prefetch_related('approvers')
        .order_by('mission__created_at')  # or by position, etc.
    )

    # If you need just missions (deduped), use:
    # missions_qs = Mission.objects.filter(flows__in=flows_qs).distinct()

    return render(request, 'Missions/my_pending_approvals.html', {
        'flows': flows_qs,  # each row = a step you must approve
    })

from django.contrib import messages

@login_required
@require_POST
def approve_flow(request, flow_id: int):
    flow = get_object_or_404(
        MissionFlow,
        pk=flow_id,
        is_current=True,
        approvers=request.user,
    )
    MissionApproval.objects.update_or_create(
        flow=flow,
        user=request.user,
        defaults={'approved': True},
    )
    flow.approved = True
    flow.save()
    messages.success(request, "Approved.")
    return redirect('my_pending_approvals')