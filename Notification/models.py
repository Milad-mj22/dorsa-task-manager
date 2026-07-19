from django.db import models

# Create your models here.
from django.conf import settings
from django.db import models
from django.contrib.auth.models import User


class NotificationStep(models.Model):
    """
    One 'part' or 'step' in your app where you MAY send notifications.
    Example: 'ORDER_CREATED', 'PAYMENT_FAILED', 'NEW_TASK_ASSIGNED'
    """
    code = models.CharField(max_length=100, unique=True)  # used in decorator
    name = models.CharField(max_length=200)               # human readable
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.name} ({self.code})"


class NotificationPreference(models.Model):
    """
    For each (user, step) say what they want to receive.
    """
    CHANNEL_PUSH = "push"
    CHANNEL_MESSAGE = "message"
    CHANNEL_BOTH = "both"
    CHANNEL_NONE = "none"

    CHANNEL_CHOICES = [
        (CHANNEL_PUSH, "Push only"),
        (CHANNEL_MESSAGE, "Message only"),
        (CHANNEL_BOTH, "Push + Message"),
        (CHANNEL_NONE, "Nothing"),
    ]

    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, verbose_name='کابران ارسالی')

    step = models.ForeignKey(NotificationStep, on_delete=models.CASCADE)
    channel = models.CharField(
        max_length=20,
        choices=CHANNEL_CHOICES,
        default=CHANNEL_BOTH,
    )
    enabled = models.BooleanField(default=True)

    class Meta:
        unique_together = ("user", "step")

    def __str__(self):
        return f"{self.user} - {self.step} ({self.channel}, enabled={self.enabled})"
