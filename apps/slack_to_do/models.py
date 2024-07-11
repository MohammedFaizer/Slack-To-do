from django.db import models


class Watcher(models.Model):
    slack_user_id = models.CharField(max_length=255)

    def __str__(self):
        return self.slack_user_id


class Task(models.Model):
    id = models.AutoField(primary_key=True)
    task_name = models.CharField(max_length=255)
    due_date = models.DateField()
    task_assignee = models.CharField(max_length=255)
    task_channel_id = models.CharField(max_length=255)
    task_notes = models.TextField()
    is_complete = models.BooleanField(default=False)
    watchers = models.ManyToManyField(Watcher, related_name="tasks_watching")

    def __str__(self):
        return self.task_name


class SlackMessage(models.Model):
    channel_id = models.CharField(max_length=50, unique=True)
    ts = models.CharField(
        max_length=50
    )  # Assuming ts is a string, adjust as per Slack API response

    def __str__(self):
        return f"Slack message for channel {self.channel_id}"
