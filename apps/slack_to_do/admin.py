from django.contrib import admin

# Register your models here.
from .models import SlackMessage, Task, Watcher

admin.site.register(Task)
admin.site.register(SlackMessage)
admin.site.register(Watcher)
