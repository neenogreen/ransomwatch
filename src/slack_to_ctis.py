import logging
import sys
import traceback
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
import time
from config import Config
from notifications.ctis import CTISNotification
from notifications.slack import SlackNotification
from db.models import Victim
from datetime import datetime
import os

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
            timestamp = float(f.read().strip("\n"))
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
        SlackNotification.send_error_notification(
                Config["slack_to_ctis"]["slack_error_url"],
                f"Slack to ctis -> Error getting messages: {e}",
                traceback.format_exc().strip())
        os._exit(1)

    ctis_messages = 0

    for e in reversed(conversation_history):
        if timestamp >= float(e["ts"]):
            continue
        timestamp = float(e["ts"])
        if not "New Victim Posted" in str(e):
            continue
        if not "subtype" in e.keys():
            continue
        if e["subtype"] != "bot_message":
            continue

        try:
            actor = e["attachments"][0]["blocks"][1]["fields"][0]["text"].split("\n")[1]
            if "??" in e["attachments"][0]["blocks"][1]["fields"][1]["text"] or "**" in  e["attachments"][0]["blocks"][1]["fields"][1]["text"]:
                continue
            if "http" in e["attachments"][0]["blocks"][1]["fields"][1]["text"]:
                name = e["attachments"][0]["blocks"][1]["fields"][1]["text"].split("\n")[1][1:].split("|")[0]
            else:
                name = e["attachments"][0]["blocks"][1]["fields"][1]["text"].split("\n")[1]
            if "PUBLISHED" in name and "Lockbit" in actor:
                continue
            published = datetime.strptime(e["attachments"][0]["blocks"][1]["fields"][2]["text"].split("\n")[1], "%b %d, %Y")
            try:
                first_seen = datetime.strptime(e["attachments"][0]["blocks"][1]["fields"][3]["text"].split("\n")[1], "%b %d, %Y at %H:%M:%S UTC")
            except:
                first_seen = None
            try:
                description = e["attachments"][0]["blocks"][1]["fields"][4]["text"][14:]
            except:
                description = ""
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
            SlackNotification.send_error_notification(
                    Config["slack_to_ctis"]["slack_error_url"],
                    f"Slack to ctis -> Failed uploading to ctis: {name}",
                    traceback.format_exc().strip())
            os._exit(1)

        ctis_messages += 1

    logging.info("{} CTIS messages sent".format(ctis_messages, channel_id))

    with open(Config["slack_to_ctis"]["time_path"], "w") as f:
        f.write(str(timestamp))

if __name__ == "__main__":
    try:
        main(sys.argv)
    except:
        logging.error(f"Got a fatal error")
        SlackNotification.send_error_notification(
                Config["slack_to_ctis"]["slack_error_url"],
                f"Slack to ctis -> Got a fatal error",
                traceback.format_exc().strip())
