import logging
import os
from slack_bolt import App, logger
import mysql.connector
from slack_sdk import WebClient
logging.basicConfig(level=logging.DEBUG)
from slack_sdk.errors import SlackApiError
# Initializes your app with your bot token and signing secret
app = App(
    token=os.environ.get("SLACK_BOT_TOKEN"),
    signing_secret=os.environ.get("SLACK_SIGNING_SECRET")
)
slack_token = os.environ["SLACK_BOT_TOKEN"]
client = WebClient(token=slack_token)



#database connection
mydb = mysql.connector.connect(
  host=os.environ.get("DBHOST"),
  user=os.environ.get("DBUSER"),
  password=os.environ.get("DBPASSWORD"),
  database=os.environ.get("DBDATABASE"),
  raise_on_warnings= True
)

#middleware
@app.middleware  # or app.use(log_request)
def log_request(logger, body, next):
    logger.debug(body)
    return next()


def track_task():
    return ""

def get_projectslackchannelsid_from_channelid(channel_id):
    mycursor = mydb.cursor()
    sql = """SELECT project_slack_channels_id FROM project_slack_channels where channel_id = %s"""
    mycursor.execute(sql , (channel_id,))
    myresult = mycursor.fetchone()
    return myresult[0]

def insert_create_task(project_slack_channels_id):
    mycursor = mydb.cursor()
    sql = """INSERT INTO tasks (project_slack_channels_id) VALUES (%s)"""
    mycursor.execute(sql , (project_slack_channels_id,))
    mydb.commit()
    return 1

def insert_task_detail(task_id,name,value):
    mycursor = mydb.cursor()
    sql = """INSERT INTO task_details (task_id,name,value) VALUES (%s,%s,%s)"""
    mycursor.execute(sql , (task_id,name,value,))
    mydb.commit()
    return 1    

def create_task(task_name , severity , user_id,username, channel_id):
    project_slack_channels_id = get_projectslackchannelsid_from_channelid(channel_id)
#check if project_id is present 
    if project_slack_channels_id:
        task_id = insert_create_task(project_slack_channels_id)
        if task_id:
            res_task_name = insert_task_detail(task_id,"task_name",task_name)
            res_severity = insert_task_detail(task_id,"severity",severity)
            res_severity = insert_task_detail(task_id,"creator",user_id)
            if res_task_name and res_severity:
                return f"Created Ticket: {task_name} TicketID: {task_id} By: {username} with Severity Level: {severity}"
            else:
                return "Error creating Ticket details"
        else:
            return "Error Creating Ticket"
    else:
        return "Error Project Not Found"

def chat_send_message(channel_id,result):
    try:
        response = client.chat_postMessage(
            channel=channel_id,
            text=result        )
    except SlackApiError as e:
        # You will get a SlackApiError if "ok" is False
        assert e.response["error"]    # str like 'invalid_auth', 'channel_not_found'


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
def handle_create_command(body, ack, respond, client, logger):
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
def handle_severity_option(ack, body, logger):
    ack()



@app.view("view-id")
def view_submission(ack, body, logger):
    ack()
    user_id = body["user"]["id"]
    username= body["user"]["username"]
    channel_id = body["view"]["private_metadata"]
    arrval = body["view"]["state"]["values"]
    task_name_key = next(iter(arrval["task_name"]))
    task_name = arrval["task_name"][task_name_key]["value"]
    severity_key = next(iter(arrval["severity"]))
    severity = arrval["severity"]["static_select-action"]["selected_option"]["value"]
    ack()
    result = create_task(task_name , severity , user_id,username, channel_id)
    chat_send_message(channel_id,result)
    logger.info(result)


@app.error
def global_error_handler(error, body, logger):
    logger.exception(error)
    logger.info(body)


# Start your app
if __name__ == "__main__":
    app.start(3000)

