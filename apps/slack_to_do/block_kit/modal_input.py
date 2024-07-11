payload = {
    "type": "modal",
    "callback_id": "task_submission",
    "title": {"type": "plain_text", "text": "Task Planner", "emoji": True},
    "submit": {"type": "plain_text", "text": "Add Task", "emoji": True},
    "close": {"type": "plain_text", "text": "Cancel", "emoji": True},
    "blocks": [
        {
            "type": "input",
            "block_id": "TSK01",
            "element": {"type": "plain_text_input", "action_id": "title_text_input-action"},
            "label": {"type": "plain_text", "text": "Task Title✨", "emoji": True},
        },
        {
            "type": "input",
            "block_id": "TSK02",
            "element": {
                "type": "datepicker",
                "placeholder": {"type": "plain_text", "text": "Select a date", "emoji": True},
                "action_id": "due_date-action",
            },
            "label": {"type": "plain_text", "text": "Due Date📆", "emoji": True},
        },
        {
            "type": "input",
            "block_id": "TSK03",
            "element": {
                "type": "users_select",
                "placeholder": {"type": "plain_text", "text": "Select a user", "emoji": True},
                "action_id": "assignee_users_select-action",
            },
            "label": {"type": "plain_text", "text": "Assignee 👨🏼‍💻", "emoji": True},
        },
        {
            "type": "input",
            "block_id": "TSK04",
            "element": {
                "type": "channels_select",
                "placeholder": {"type": "plain_text", "text": "Select a Channel", "emoji": True},
                "action_id": "channel_select-action",
            },
            "label": {"type": "plain_text", "text": "Channels #️⃣", "emoji": True},
        },
        {
            "type": "input",
            "block_id": "TSK05",
            "element": {
                "type": "plain_text_input",
                "multiline": True,
                "action_id": "notes_plain_text_input-action",
            },
            "label": {"type": "plain_text", "text": "Notes📝", "emoji": True},
        },
        {
            "type": "input",
            "block_id": "TSK06",
            "element": {
                "type": "multi_users_select",
                "placeholder": {"type": "plain_text", "text": "Select Watchers", "emoji": True},
                "action_id": "watcher_multi_users_select-action",
            },
            "label": {"type": "plain_text", "text": "Watcher", "emoji": True},
        },
    ],
}
