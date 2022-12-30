import logging
import sys
import traceback
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
import time
from config import Config
from notifications.ctis import CTISNotification
from db.models import Victim
from datetime import datetime

logging.basicConfig(
    format="%(asctime)s [%(levelname)s] %(message)s",
    level=logging.INFO,
    datefmt="%Y/%m/%d %H:%M:%S",
    handlers=[
        logging.StreamHandler()
    ]
)

def main(argv):
    try:
        with open(Config["slack_to_ctis"]["time_path"], "r") as f:
            timestamp = float(f.readline()[:-1])
    except:
        with open(Config["slack_to_ctis"]["time_path"], "w") as f:
            timestamp = time.time()
            f.write(str(timestamp))
    
    client = WebClient(token=Config["slack_to_ctis"]["slack"]["token"])
    conversation_history = []
    channel_id = Config["slack_to_ctis"]["slack"]["channel_id"]

    try:
        result = client.conversations_history(channel=channel_id,
                inclusive=False,
                oldest=timestamp)
        conversation_history = result["messages"]
        logging.info("{} messages found in {}".format(len(conversation_history), channel_id))
    except SlackApiError as e:
        logging.error("Error getting messages: {}".format(e))

    for e in reversed(conversation_history):
        timestamp = float(e["ts"])
        if not "subtype" in e.keys():
            continue
        if e["subtype"] != "bot_message":
            continue

        try:
            actor = e["attachments"][0]["blocks"][1]["fields"][0]["text"].split("\n")[1]
            try:
                name = e["attachments"][0]["blocks"][1]["fields"][1]["text"].split("\n")[1][1:].split("|")[0]
            except:
                name = e["attachments"][0]["blocks"][1]["fields"][1]["text"].split("\n")
            published = datetime.strptime(e["attachments"][0]["blocks"][1]["fields"][2]["text"].split("\n")[1], "%b %d, %Y")
            first_seen = datetime.strptime(e["attachments"][0]["blocks"][1]["fields"][3]["text"].split("\n")[1], "%b %d, %Y at %H:%M:%S UTC")
            description = e["attachments"][0]["blocks"][1]["fields"][4]["text"][14:]
            victim_leak_site = e["attachments"][0]["blocks"][2]["fields"][0]["text"][1:-18]
            v = Victim(name=name, url=victim_leak_site,
                    description=description,
                    published=published,
                    first_seen=first_seen,
                    last_seen=datetime.utcnow(),
                    site=0)
            notification = CTISNotification(Config["slack_to_ctis"]["ctis"]["url"],
                    Config["slack_to_ctis"]["ctis"]["username"],
                    Config["slack_to_ctis"]["ctis"]["password"])
            notification.send_new_victim_notification(v, actor)
        except:
            logging.error(f"Failed uploading to ctis: {name}")
            continue

    with open(Config["slack_to_ctis"]["time_path"], "w") as f:
        f.write(str(timestamp))

if __name__ == "__main__":
    try:
        main(sys.argv)
    except:
        logging.error(f"Got a fatal error")
        tb = traceback.format_exc()
        logging.error(tb.strip())  # there is a trailing newline
