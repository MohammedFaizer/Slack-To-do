import logging

from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from rest_framework.views import APIView
from slack_bolt.adapter.django import SlackRequestHandler

from .slack_listeners import app

handler = SlackRequestHandler(app=app)


class Slack_Events_Handler(APIView):
    def post(self, request):
        # print(f"Incoming request data: {request.body.decode('utf-8')}")
        return handler.handle(request)
