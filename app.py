import logging
import os
from slack_bolt import App

logging.basicConfig(level=logging.DEBUG)
# Initializes your app with your bot token and signing secret
app = App(
    token=os.environ.get("SLACK_BOT_TOKEN"),
    signing_secret=os.environ.get("SLACK_SIGNING_SECRET")
)

# Listens to incoming messages that contain "hello"
# To learn available listener arguments,
# visit https://slack.dev/bolt-python/api-docs/slack_bolt/kwargs_injection/args.html


@app.middleware  # or app.use(log_request)
def log_request(logger, body, next):
    logger.debug(body)
    return next()

def track_task():
    return "Hello from track_task"

def create_task(rask_name , task_sever , task_user):
    return "{task_name} , {task_sever} , {task_user}"



@app.command("/track")
def project_command(ack, body):
    channel_name = body["channel_name"]
    channel_id = body["channel_id"]
    command = body["text"]
    command_chunks = command.split()
    track_com = command_chunks[1]
    task_id_str = command_chunks[0]
    func_track_task_out = track_task() 
    if task_id_str.isnumeric():
        task_id=int(task_id_str)
        if track_com == "start": 
            ack(f"⏱️  Started tracking time for project {channel_name} , task : {task_id}  {func_track_task_out}"  )
        elif track_com == "stop":
            ack(f"⏱️ ✅ Stoped tracking time for project {channel_name} , task : {task_id} ")
        else:
            ack(f"🤬 incorrect command usage , please use either start or stop to track task time")
    else:
            ack(f"🤬 incorrect command usage , provide task ID , use /list to list tasks and tasks ID")




@app.command("/create")
def handle_command(body, ack, respond, client, logger):
    ack()
    channel_id = body["channel_id"]
    respond()
    res = client.views_open(
        trigger_id=body["trigger_id"],
        view={
            "type": "modal",
            "callback_id": "view-id",
            "title": {
                "type": "plain_text",
                "text": "Create a New Task",
            },
            "submit": {
                "type": "plain_text",
                "text": "Submit",
            },
            "close": {
                "type": "plain_text",
                "text": "Cancel",
            },
            "private_metadata": channel_id,
            "blocks": [
                {
                    "type": "input",
                    "block_id" : "task_name",
                    "element": {"type": "plain_text_input"},
                    "label": {
                        "type": "plain_text",
                        "text": "Task Name",
                    },
                },

		{
			"type": "section",
                        "block_id" : "severity",
			"text": {
				"type": "mrkdwn",
				"text": "Select Severity Level"
			},
			"accessory": {
				"type": "static_select",
				"placeholder": {
					"type": "plain_text",
					"text": "Severity Level",
				},
				"options": [
					{
						"text": {
							"type": "plain_text",
							"text": "Urgent",
						},
						"value": "urgent"
					},
					{
						"text": {
							"type": "plain_text",
							"text": "High",
						},
						"value": "high"
					},
					{
						"text": {
							"type": "plain_text",
							"text": "Normal",
						},
						"value": "normal"
					}
				],
				"action_id": "static_select-action"
			}
		},


                ],
        },
    )


@app.action("static_select-action")
def handle_some_action(ack, body, logger):
    ack()



@app.view("view-id")
def view_submission(ack, body, logger):
    ack()
    user_id = body["user"]["id"]
    channel_id = body["view"]["private_metadata"]
    task_name = "1"
    severity = "2"
    arrval = body["view"]["state"]["values"]
    task_name_key = next(iter(arrval["task_name"]))
    task_name = arrval["task_name"][task_name_key]["value"]
    severity_key = next(iter(arrval["severity"]))
    severity = arrval["severity"]["static_select-action"]["selected_option"]["value"]
    ack()
    logger.info(severity)


@app.error
def global_error_handler(error, body, logger):
    logger.exception(error)
    logger.info(body)


# Start your app
if __name__ == "__main__":
    app.start(3000)

