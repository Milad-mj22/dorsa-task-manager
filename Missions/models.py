from django.db import models
from django.contrib.auth.models import User
from django.db import models, transaction
from django.utils import timezone
from django.core.exceptions import ValidationError
# Create your models here.



class MissionType(models.Model):
    """Business category of mission, each with its own approval flow template."""
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name


class Mission(models.Model):
    from Projects.models import Project
    STATUS_CHOICES = [
        ('pending', 'در انتظار تایید'),
        ('approved', 'تایید شده'),
        ('in_progress', 'در حال انجام'),
        ('completed', 'تکمیل شده'),
        ('rejected', 'رد شده'),
    ]

    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="missions")
    type = models.ForeignKey(MissionType, on_delete=models.PROTECT, related_name="missions",null=True,blank=True)

    location = models.CharField(max_length=255)
    persons = models.ManyToManyField(User, related_name="missions")
    price = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    description = models.TextField(blank=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name="created_missions")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    goals = models.TextField(blank=True)

    start_date = models.DateTimeField()
    end_date = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.project.name} - {self.location} "

    def steps(self):
        return self.flows.order_by('position')

    def get_current_step(self):
        return self.flows.filter(is_current=True).order_by('position').first()

    def is_fully_approved(self):
        return not self.flows.filter(approved=False).exists()

    @property
    def progress_percent(self):
        total = self.flows.count()
        if not total:
            return 0
        done = self.flows.filter(approved=True).count()
        return round(100 * done / total)

    @transaction.atomic
    def start_flow(self):
        if not self.flows.exists():
            return
        if not self.flows.filter(is_current=True).exists():
            first = self.flows.order_by('position').first()
            first.is_current = True
            first.started_at = timezone.now()
            first.save(update_fields=['is_current', 'started_at'])

    @transaction.atomic
    def recompute_status_from_flow(self):
        if self.is_fully_approved():
            if self.status != 'approved':
                self.status = 'approved'
                self.save(update_fields=['status'])
        else:
            if self.status == 'approved':
                self.status = 'pending'
                self.save(update_fields=['status'])

    # ---- NEW: Instantiate steps from the selected type’s template
    @transaction.atomic
    def bootstrap_flow_from_type(self):
        """
        Create MissionFlow steps from the MissionType's FlowStepTemplate set.
        Safe to call only once per mission.
        """
        if self.flows.exists():
            return  # already bootstrapped

        step_templates = (
            FlowStepTemplate.objects
            .filter(flow__mission_type=self.type)
            .select_related('flow')
            .prefetch_related( 'approver_users')
            .order_by('position')
        )
        if not step_templates.exists():
            raise ValidationError(f"No flow template is defined for '{self.type}'.")

        for tpl in step_templates:
            step = MissionFlow.objects.create(
                mission=self,
                step_name=tpl.step_name,
                description=tpl.description,
                position=tpl.position,
                created_by=self.created_by,
            )
            # Resolve approvers from template: users + users in groups
            approvers_qs = tpl.approver_users.all()
            # if tpl.approver_groups.exists():
            #     group_user_ids = User.objects.filter(groups__in=tpl.approver_groups.all()).values_list('id', flat=True).distinct()
            #     approvers_qs = User.objects.filter(id__in=set(list(approvers_qs.values_list('id', flat=True)) + list(group_user_ids)))
            step.approvers.set(approvers_qs)

        self.start_flow()

class MissionFlow(models.Model):
    mission = models.ForeignKey(Mission, on_delete=models.CASCADE, related_name="flows")
    step_name = models.CharField(max_length=255)
    description = models.TextField(blank=True)

    position = models.PositiveIntegerField()
    is_current = models.BooleanField(default=False)
    approved = models.BooleanField(default=False)
    started_at = models.DateTimeField(null=True, blank=True)
    finished_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)

    approvers = models.ManyToManyField(User, related_name="missionflow_approvers", blank=True)

    class Meta:
        ordering = ['mission', 'position']
        unique_together = [('mission', 'position')]
        indexes = [
            models.Index(fields=['mission', 'position']),
            models.Index(fields=['mission', 'is_current']),
        ]

    def __str__(self):
        return f"{self.mission} - Step {self.position}: {self.step_name}"

    @property
    def pending_approvers(self):
        required = self.approvers.all()
        done_user_ids = self.approvals.filter(approved=True).values_list('user_id', flat=True)
        return required.exclude(id__in=list(done_user_ids))

    def _mark_done(self):
        self.approved = True
        self.is_current = False
        self.finished_at = timezone.now()
        self.save(update_fields=['approved', 'is_current', 'finished_at'])

    @transaction.atomic
    def recompute_and_maybe_advance(self):
        all_approved = not self.approvers.exists() or not self.pending_approvers.exists()
        if all_approved and not self.approved:
            self._mark_done()
            next_step = self.mission.flows.filter(position__gt=self.position).order_by('position').first()
            if next_step:
                if not next_step.is_current:
                    next_step.is_current = True
                    next_step.started_at = next_step.started_at or timezone.now()
                    next_step.save(update_fields=['is_current', 'started_at'])
            self.mission.recompute_status_from_flow()
        elif self.approved and self.pending_approvers.exists():
            # rollback if someone revoked
            self.approved = False
            self.finished_at = None
            if not self.mission.flows.filter(is_current=True, position__gt=self.position).exists():
                self.is_current = True
                self.started_at = self.started_at or timezone.now()
            self.save(update_fields=['approved', 'finished_at', 'is_current', 'started_at'])


class MissionApproval(models.Model):
    flow = models.ForeignKey(MissionFlow, on_delete=models.CASCADE, related_name="approvals")
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    approved = models.BooleanField(default=False)
    approved_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = [('flow', 'user')]
        indexes = [
            models.Index(fields=['flow', 'user']),
            models.Index(fields=['flow', 'approved']),
        ]

    def __str__(self):
        return f"{self.user} - {self.flow.step_name} {'✅' if self.approved else '❌'}"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        with transaction.atomic():
            flow = MissionFlow.objects.select_for_update().get(pk=self.flow_id)
            flow.recompute_and_maybe_advance()


class MissionComment(models.Model):
    mission = models.ForeignKey('Mission', on_delete=models.CASCADE, related_name='comments')
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Comment by {self.author} on {self.mission}"
    

class FlowTemplate(models.Model):
    """Container for ordered step templates of a MissionType."""
    mission_type = models.OneToOneField(MissionType, on_delete=models.CASCADE, related_name='flow_template')
    name = models.CharField(max_length=120, default="Default Flow")
    description = models.TextField(blank=True)

    def __str__(self):
        return f"{self.mission_type.name} – {self.name}"


class FlowStepTemplate(models.Model):
    flow = models.ForeignKey(FlowTemplate, on_delete=models.CASCADE, related_name='steps')
    step_name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    position = models.PositiveIntegerField()

    # Who must approve this step (either fixed users or by role/group)
    approver_users = models.ManyToManyField(User, related_name='flow_step_templates_as_user', blank=True)
    # approver_groups = models.ManyToManyField(Group, related_name='flow_step_templates_as_group', blank=True)

    class Meta:
        ordering = ['position']
        unique_together = [('flow', 'position')]

    def __str__(self):
        return f"{self.flow.mission_type.name} – {self.position}. {self.step_name}"
