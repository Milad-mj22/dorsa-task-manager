from django.db import models

# Create your models here.
from django.contrib.auth.models import User
# Create your models here.

class TicketCategory(models.Model):
    name = models.CharField(max_length=100, unique=True, verbose_name="نام دسته‌بندی")
    description = models.TextField(blank=True, null=True, verbose_name="توضیحات")
    viewers = models.ManyToManyField(User, related_name='viewable_categories', blank=True)
    is_project = models.BooleanField(default=False)  # True for only show for projects
    
    def __str__(self):
        return self.name

class Ticket(models.Model):
    STATUS_CHOICES = [
        ('open', 'باز'),
        ('in_progress', 'در حال بررسی'),
        ('closed', 'بسته شده'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='tickets', verbose_name="کاربر")
    title = models.CharField(max_length=255, verbose_name="عنوان تیکت")
    message = models.TextField(verbose_name="پیام")
    category = models.ForeignKey(TicketCategory, on_delete=models.SET_NULL, null=True, verbose_name="دسته‌بندی")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='open', verbose_name="وضعیت")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاریخ ایجاد")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="آخرین بروزرسانی")

    def __str__(self):
        return f"{self.title} - {self.user.username}"
    

class TicketMessage(models.Model):
    ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(User, on_delete=models.CASCADE)
    message = models.TextField()
    attachment = models.FileField(upload_to='ticket_attachments/', null=True, blank=True)
    sent_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Message by {self.sender.username} on {self.ticket.title}"
    





class ProjectTicket(models.Model):
    STATUS_CHOICES = [
        ('open', 'باز'),
        ('in_progress', 'در حال بررسی'),
        ('closed', 'بسته شده'),
    ]
    phone = models.BigIntegerField(blank=True,null=True,verbose_name='شماره تماس')
    title = models.CharField(max_length=255, verbose_name="عنوان تیکت")
    message = models.TextField(verbose_name="پیام")
    category = models.ForeignKey(TicketCategory, on_delete=models.SET_NULL, null=True, verbose_name="دسته‌بندی")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='open', verbose_name="وضعیت")
    image = models.ImageField(upload_to="project_tickets/images/", blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاریخ ایجاد")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="آخرین بروزرسانی")
    project = models.ForeignKey(
        'Projects.Project',   # 👈 STRING REFERENCE
        on_delete=models.CASCADE,
        related_name='tickets',
        verbose_name='پروژه',
        null=True,
        blank=True
    )

    def __str__(self):
        return f"{self.title} - {self.project}"
    

class ProjectTicketMessage(models.Model):
    ticket = models.ForeignKey(ProjectTicket, on_delete=models.CASCADE, related_name='messages_project_ticket')
    phone = models.BigIntegerField(blank=True,null=True,verbose_name='شماره تماس')
    message = models.TextField()
    attachment = models.FileField(upload_to='ticket_attachments/', null=True, blank=True)
    sent_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Message by {self.phone} on {self.ticket.title}"