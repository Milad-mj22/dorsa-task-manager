from django.db import models

# Create your models here.
from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator
from decimal import Decimal





DEFAULT_PROJECT_ID = 1



class Team(models.Model):

    name = models.CharField(max_length=100)
    def __str__(self):
        return self.name

class Sprint(models.Model):
    name = models.CharField(max_length=100)
    start_date = models.DateField()
    end_date = models.DateField()
    is_active = models.BooleanField(default=True)
    total_hours = models.IntegerField(default=0)

    def __str__(self):
        return self.name
    
    
class Story(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    team = models.ForeignKey(Team, on_delete=models.CASCADE)
    sprint = models.ForeignKey(Sprint, on_delete=models.CASCADE)

    project = models.ForeignKey(
        'Projects.Project',
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )

    priority = models.IntegerField(default=0)


class Task(models.Model):
    STATUS_CHOICES = [
        ('todo', 'To Do'),
        ('doing', 'Doing'),
        ('done', 'Done'),
    ]

    title = models.CharField(max_length=255)
    priority = models.IntegerField(default=0)  # New field for priority
    
    description = models.TextField(blank=True)
    story = models.ForeignKey(Story, on_delete=models.CASCADE)
    # New format: precise hours, e.g., 1.5 hours
    goal_time = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.25'))],
        help_text="Estimated time to complete (in hours)"
    )
    assigned_to = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='todo')
    created_at = models.DateTimeField(auto_now_add=True)


    is_delete = models.BooleanField(default=False)
    user_delete = models.ForeignKey(User, on_delete=models.SET_NULL, null=True,related_name='user_deleted')

    def __str__(self):
        return self.title
    

class TimeEntry(models.Model):
    task = models.ForeignKey(Task, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    datetime =  models.DateTimeField()


    hours_spent = models.DecimalField(max_digits=5, decimal_places=2)

    def __str__(self):
        return f"{self.user.username} - {self.task.title} - {self.hours_spent}h"
    




class CommentTask(models.Model):

    task_id = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='task_coment')  # محصولی که تولید شده
    description = models.TextField(blank=True)
    created_date = models.DateField(verbose_name="تاریخ ایجاد",auto_now_add=True)
    assigned_to = models.ForeignKey(User, on_delete=models.CASCADE,blank=True,null=True,related_name='comment_task_assign_to')
    created_by = models.ForeignKey(User, on_delete=models.CASCADE,related_name='comment_task_assign_by')
     