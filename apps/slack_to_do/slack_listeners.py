import logging

from django.conf import settings
from slack_bolt import App
from slack_sdk.errors import SlackApiError

from .block_kit import app_home, modal_input
from .models import SlackMessage, Task, Watcher

logger = logging.getLogger(__name__)

app = App(
    token=settings.SLACK_BOT_TOKEN,
    signing_secret=settings.SLACK_SIGNING_SECRET,
    token_verification_enabled=False,
)


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


@app.event("app_home_opened")
def update_home_tab(
    client,
    event,
):
    try:
        client.views_publish(user_id=event["user"], view=app_home.payload)

        print("App Home updated successfully")
    except Exception as e:
        print(f"Error updating App Home: {e}")


@app.event("app_mention")
def handle_app_mentions(event, say):
    say(f"Hello <@{event['user']}> this is Task Guru :)")


@app.command("/add")
def add_task_command(ack, body, client):
    ack()
    handle_some_command(body["trigger_id"], client)


@app.shortcut("add_task_shortcut")
def add_task_shortcut(ack, body, client):
    ack()
    handle_some_command(body["trigger_id"], client)


def handle_some_command(body, client):
    try:
        client.views_open(trigger_id=body, view=modal_input.payload)
        print("Modal sent successfully")
    except Exception as e:
        print("This is error", e)


#


@app.view("task_submission")
def task_view_submission(ack, body, view, client):
    ack()
    print("FAAAAAAAAAAAAAAAAAAAAAAA")
    v = view["state"]["values"]
    title = v["TSK01"]["title_text_input-action"]["value"]
    due_date = v["TSK02"]["due_date-action"]["selected_date"]
    assignee = v["TSK03"]["assignee_users_select-action"]["selected_user"]
    channel_id = v["TSK04"]["channel_select-action"]["selected_channel"]
    notes = v["TSK05"]["notes_plain_text_input-action"]["value"]
    watcher_list = v["TSK06"]["watcher_multi_users_select-action"]["selected_users"]
    print(watcher_list)
    try:
        task = Task(
            task_name=title,
            due_date=due_date,
            task_assignee=assignee,
            task_channel_id=channel_id,
            task_notes=notes,
        )
        task.save()

        for slack_user_id in watcher_list:
            watcher, created = Watcher.objects.get_or_create(slack_user_id=slack_user_id)
            task.watchers.add(watcher)

        task.save()
        client.views_open(
            trigger_id=body["trigger_id"],
            view_id=body["view"]["id"],
            view={
                "type": "modal",
                "callback_id": "task_view",
                "title": {"type": "plain_text", "text": "Added Task Sucessfully👍🏼", "emoji": True},
                "close": {"type": "plain_text", "text": "Cancel", "emoji": True},
                "blocks": [
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
                    },
                ],
            },
        )
        blocks = fetch_blocks(channel_id=channel_id, iscomplete=False)
        try:
            slack_message = SlackMessage.objects.get(channel_id=channel_id)
            client.pins_remove(channel=channel_id, timestamp=slack_message.ts)
            client.chat_delete(
                channel=channel_id,
                ts=slack_message.ts,
            )
            response = client.chat_postMessage(
                channel=channel_id, blocks=blocks, text="Here are the open tickets"
            )
            slack_message.ts = response["ts"]
            slack_message.save()
            client.pins_add(channel=channel_id, timestamp=slack_message.ts)
            if watcher_list:
                for user_id in watcher_list:
                    try:
                        response = client.chat_postMessage(
                            channel=user_id,
                            blocks=[
                                {
                                    "type": "section",
                                    "text": {
                                        "type": "mrkdwn",
                                        "text": f"*<@{assignee}>* ✨ Thinks You Should Watch this task : *{title}*\n"
                                        f"*Assignee:* <@{task.task_assignee}>\t *Due date:* {task.due_date}\n"
                                        f"*Project:* <#{task.task_channel_id}>\n"
                                        f"*Watching:* {' '.join(f'<@{i}>' for i in watcher_list)}",
                                    },
                                },
                                {"type": "divider"},
                            ],
                            as_user=True,
                        )
                        print(f"Message sent to user {user_id}")

                    except Exception as e:
                        print(f"Error sending message to user {user_id}: {str(e)}")

        except SlackMessage.DoesNotExist:
            response = client.chat_postMessage(
                channel=channel_id, blocks=blocks, text="Here are the open tickets"
            )
            try:
                SlackMessage.objects.create(channel_id=channel_id, ts=response["ts"])
                client.pins_add(channel=channel_id, timestamp=response["ts"])
            except Exception as e:
                print(f"Error storing message metadata: {e}")

        except Exception as e:
            print(f"Error updating or sending message: {e}")

    except Exception as e:
        print("This is error", e)


@app.action("complete_task_home")
def handle_complete_task_home(ack, body, client):
    ack()
    try:
        action_value = body["actions"][0]["value"]
        user_id = body["user"]["id"]
        task_id = int(action_value)
        task = Task.objects.get(id=task_id)
        task.is_complete = True
        task.save()
        channel_id = task.task_channel_id
        blocks = fetch_blocks(channel_id=channel_id, iscomplete=False)
        try:
            slack_message = SlackMessage.objects.get(channel_id=channel_id)
            response = client.chat_update(
                channel=channel_id,
                ts=slack_message.ts,
                blocks=blocks,
                text="Here are the open tickets",
            )
            current_blocks = app_home.payload["blocks"]
            updated_blocks = current_blocks + blocks
            opened_tasks_payload = {
                "type": "home",
                "blocks": updated_blocks,
            }
            client.views_publish(user_id=user_id, view=opened_tasks_payload)
            watchy = task.watchers.all().values()
            print(watchy)
            if watchy:
                for i in watchy:
                    client.chat_postMessage(
                        channel=i["slack_user_id"],
                        blocks=[
                            {
                                "type": "section",
                                "text": {
                                    "type": "mrkdwn",
                                    "text": f"*✅<@{task.task_assignee}>* Just Completed the task : *{task.task_name}*\n"
                                    f"*Assignee:* <@{task.task_assignee}>\t *Due date:* {task.due_date}\n"
                                    f"*Project:* <#{task.task_channel_id}>\n",
                                },
                            },
                            {"type": "divider"},
                        ],
                        as_user=True,
                    )
            print(f"Updated home view for user {user_id} successfully.")
        except SlackApiError as e:
            error_msg = f"Error updating home view: {e.response['error']}"
            print(error_msg)  # Extend the list with new blocks

        except SlackMessage.DoesNotExist:
            # Handle case where slack_message does not exist
            print(f"Slack message metadata for channel {channel_id} does not exist.")
            client.chat_postMessage(
                channel=channel_id, text="An error occurred while updating the message."
            )

        except Exception as e:
            # Handle any other errors
            print(f"Error updating message: {e}")
            client.chat_postMessage(
                channel=channel_id, text="An error occurred while updating the message."
            )

    except Task.DoesNotExist:
        print(f"Task with ID {task_id} does not exist.")
        client.chat_postMessage(
            channel=channel_id, text="The task you're trying to complete does not exist."
        )
    except Exception as e:
        print(f"Error handling complete task action: {e}")
        client.chat_postMessage(
            channel=channel_id, text="An error occurred while processing your request."
        )


@app.action("complete_task")
def handle_complete_task(ack, body, client):
    ack()

    try:
        # Extract the necessary details from the action payload
        action_value = body["actions"][0]["value"]
        channel_id = body["channel"]["id"]
        # Get the task ID from the action value
        task_id = int(action_value)
        # Update the task status to complete
        task = Task.objects.get(id=task_id)
        task.is_complete = True
        task.save()
        # Fetch updated task list
        blocks = fetch_blocks(channel_id=channel_id, iscomplete=False)
        # Update the original message with the new list of tasks
        try:
            slack_message = SlackMessage.objects.get(channel_id=channel_id)
            response = client.chat_update(
                channel=channel_id,
                ts=slack_message.ts,
                blocks=blocks,
                text="Here are the open tickets",
            )
            watchy = task.watchers.all().values()
            print(watchy)
            if watchy:
                for i in watchy:
                    client.chat_postMessage(
                        channel=i["slack_user_id"],
                        # text=(
                        # f"*✨<@{task.task_assignee}>* Just Completed the task : *{task.task_name}*\n"
                        # f"*Assignee:* <@{task.task_assignee}>\t *Due date:* {task.due_date}\n"
                        # f"*Project:* <#{task.task_channel_id}>\n"
                        # ),
                        blocks=[
                            {
                                "type": "section",
                                "text": {
                                    "type": "mrkdwn",
                                    "text": f"*✅<@{task.task_assignee}>* Just Completed the task : *{task.task_name}*\n"
                                    f"*Assignee:* <@{task.task_assignee}>\t *Due date:* {task.due_date}\n"
                                    f"*Project:* <#{task.task_channel_id}>\n",
                                },
                            },
                            {"type": "divider"},
                        ],
                        as_user=True,
                    )
        except SlackMessage.DoesNotExist:
            # Handle case where slack_message does not exist
            print(f"Slack message metadata for channel {channel_id} does not exist.")
            client.chat_postMessage(
                channel=channel_id, text="An error occurred while updating the message."
            )

        except Exception as e:
            # Handle any other errors
            print(f"Error updating message: {e}")
            client.chat_postMessage(
                channel=channel_id, text="An error occurred while updating the message."
            )

    except Task.DoesNotExist:
        print(f"Task with ID {task_id} does not exist.")
        client.chat_postMessage(
            channel=channel_id, text="The task you're trying to complete does not exist."
        )
    except Exception as e:
        print(f"Error handling complete task action: {e}")
        client.chat_postMessage(
            channel=channel_id, text="An error occurred while processing your request."
        )


@app.action("openbtn_home_action")
def openbtn_home_action(ack, body, client):
    ack()
    user_id = body["user"]["id"]
    blocks = fetch_user_blocks(user_id=user_id, iscomplete=False)
    current_blocks = app_home.payload["blocks"]
    updated_blocks = current_blocks + blocks
    opened_tasks_payload = {"type": "home", "blocks": updated_blocks}
    try:
        client.views_publish(user_id=user_id, view=opened_tasks_payload)
        print(f"Updated home view for user {user_id} successfully.")
    except SlackApiError as e:
        error_msg = f"Error updating home view: {e.response['error']}"
        print(error_msg)  # Extend the list with new blocks


@app.action("completebtn_home_action")
def completebtn_home_action(ack, body, client):
    ack()
    user_id = body["user"]["id"]
    blocks = fetch_user_blocks(user_id=user_id, iscomplete=True)
    current_blocks = app_home.payload["blocks"]
    updated_blocks = current_blocks + blocks
    complete_tasks_payload = {"type": "home", "blocks": updated_blocks}
    try:
        client.views_publish(user_id=user_id, view=complete_tasks_payload)
        print(f"Updated home view for user {user_id} successfully.")
    except SlackApiError as e:
        error_msg = f"Error updating home view: {e.response['error']}"
        print(error_msg)  # Extend the list with new blocks
