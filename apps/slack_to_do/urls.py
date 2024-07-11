from django.urls import path

from .views import Slack_Events_Handler

urlpatterns = [
    path("slack/events", Slack_Events_Handler.as_view(), name="slack_events"),
]
