# some_app/services.py
from decorators import notify_step


@notify_step(
    "TASK_ASSIGNED",
    get_users=lambda result, *args, **kwargs: [result.assigned_to],
    get_payload=lambda result, *args, **kwargs: {
        "title": "New task assigned",
        "body": f"You have a new task: {result.title}",
        "extra": {"task_id": result.id},
    },
)
def assign_task(task, user):
    task.assigned_to = user
    task.save()
    return task
