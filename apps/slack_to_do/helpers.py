from .block_kit import modal_input
from .models import Task


def fetch_blocks(channel_id, iscomplete=None):
    tasks = Task.objects.filter(task_channel_id=channel_id, is_complete=iscomplete)
    blocks = [
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*{tasks.count()} {'open' if not iscomplete else 'closed'} ticket(s) for channel <#{channel_id}>*",
            },
        },
        {"type": "divider"},
    ]
    for task in tasks:
        blocks.append(
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": (
                        f"*Taskname:* {task.task_name}\n"
                        f"*Assignee:* <@{task.task_assignee}>\n"
                        f"*Due date:* {task.due_date}\n"
                        f"*Channel ID:* <#{task.task_channel_id}>"
                    ),
                },
            }
        )
        blocks.append(
            {
                "type": "actions",
                "elements": [
                    {
                        "type": "button",
                        "text": {"type": "plain_text", "text": "Complete"},
                        "style": "primary",
                        "value": str(task.id),
                        "action_id": "complete_task",
                    }
                ],
            }
        )
        blocks.append({"type": "divider"})
    return blocks


def fetch_user_blocks(user_id, iscomplete=None):
    tasks = Task.objects.filter(task_assignee=user_id, is_complete=iscomplete)
    blocks = [
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*{tasks.count()} {'open' if not iscomplete else 'closed'} ticket(s) for <#{user_id}>*",
            },
        },
        {"type": "divider"},
    ]
    for task in tasks:
        blocks.append(
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": (
                        f"*Taskname:* {task.task_name}\n"
                        f"*Assignee:* <@{task.task_assignee}>\n"
                        f"*Due date:* {task.due_date}\n"
                        f"*Channel ID:* <#{task.task_channel_id}>"
                    ),
                },
            }
        )
        blocks.append(
            {
                "type": "actions",
                "elements": [
                    {
                        "type": "button",
                        "text": {"type": "plain_text", "text": "Complete"},
                        "style": "primary",
                        "value": str(task.id),
                        "action_id": "complete_task_home",
                    }
                ],
            }
        ) if not iscomplete else None
        blocks.append({"type": "divider"})
    return blocks


def handle_some_command(body, client):
    try:
        client.views_open(trigger_id=body, view=modal_input.payload)
        print("Modal sent successfully")
    except Exception as e:
        print("This is error", e)
