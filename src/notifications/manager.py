import logging

from config import Config
from db.models import Site, Victim
from .slack import SlackNotification
from .discord import DiscordNotification
from .teams import TeamsNotification
from .ctis import CTISNotification
from .telegram import TelegramNotification

class NotificationManager():
    def send_new_victim_notification(victim: Victim):
        if "notifications" in Config and Config["notifications"]:
            for dest, params in Config["notifications"].items():
                if not params["new_victims"]:
                    continue

                if params["type"] == "slack":
                    if not SlackNotification.send_new_victim_notification(params["url"], victim):
                        logging.error(f"Failed to send new victim notification to Slack workspace \"{dest}\"")
                elif params["type"] == "teams":
                    if not TeamsNotification.send_new_victim_notification(params["url"], victim):
                        logging.error(f"Failed to send new victim notification to Teams channel \"{dest}\"")
                elif params["type"] == "discord":
                    if not DiscordNotification.send_new_victim_notification(params["url"], victim):
                        logging.error(f"Failed to send new victim notification to Discord guild \"{dest}\"")
                elif params["type"] == "ctis":
                    ctis_instance = CTISNotification(params["url"], params["username"], params["password"])
                    if not ctis_instance.send_new_victim_notification(victim):
                        logging.error(f"Failed to send new victim notification to CTIS \"{dest}\"")
                elif params["type"] == "telegram":
                    if not TelegramNotification.send_new_victim_notification(params["token"], params["chat_id"], victim):
                        logging.error(f"Failed to send new victim notification to Telegram \"{dest}\"")
                else:
                    logging.error(f"Attempted to send a new victim notification to an unsupported notification type: {params['type']}")
    
    def send_victim_removed_notification(victim: Victim):
        if "notifications" in Config and Config["notifications"]:
            for dest, params in Config["notifications"].items():
                if not params["removed_victims"]:
                    continue

                if params["type"] == "slack":
                    if not SlackNotification.send_victim_removed_notification(params["url"], victim):
                        logging.error(f"Failed to send removed victim notification to Slack workspace \"{dest}\"")
                elif params["type"] == "teams":
                    if not TeamsNotification.send_victim_removed_notification(params["url"], victim):
                        logging.error(f"Failed to send removed victim notification to Teams channel \"{dest}\"")
                elif params["type"] == "discord":
                    if not DiscordNotification.send_victim_removed_notification(params["url"], victim):
                        logging.error(f"Failed to send removed victim notification to Discord guild \"{dest}\"")
                else:
                    logging.error(f"Attempted to send a removed victim notification to an unsupported notification type: {params['type']}")
    
    def send_site_down_notification(site: Site):
        if "notifications" in Config and Config["notifications"]:
            for dest, params in Config["notifications"].items():
                if not params["down_sites"]:
                    continue
                if params["type"] == "slack":
                    if not SlackNotification.send_site_down_notification(params["url"], site):
                        logging.error(f"Failed to send site down notification to Slack workspace \"{dest}\"")
                elif params["type"] == "teams":
                    if not TeamsNotification.send_site_down_notification(params["url"], site):
                        logging.error(f"Failed to send site down notification to Teams channel \"{dest}\"")
                elif params["type"] == "discord":
                    if not DiscordNotification.send_site_down_notification(params["url"], site):
                        logging.error(f"Failed to send site down notification to Discord guild \"{dest}\"")
                else:
                    logging.error(f"Attempted to send a site down notification to an unsupported notification type: {params['type']}")
    
    def send_error_notification(context: str, error: str, fatal: bool = False):
        if "notifications" in Config and Config["notifications"]:
            for dest, params in Config["notifications"].items():
                if not params["errors"]:
                    continue

                if params["type"] == "slack":
                    if not SlackNotification.send_error_notification(params["url"], context, error, fatal):
                        logging.error(f"Failed to send error notification to Slack workspace \"{dest}\"")
                elif params["type"] == "teams":
                    if not TeamsNotification.send_error_notification(params["url"], context, error, fatal):
                        logging.error(f"Failed to send error notification to Teams channel \"{dest}\"")
                elif params["type"] == "discord":
                    if not DiscordNotification.send_error_notification(params["url"], context, error, fatal):
                        logging.error(f"Failed to send error notification to Discord guild \"{dest}\"")
                else:
                    logging.error(f"Attempted to send a site down notification to an unsupported notification type: {params['type']}")

    def send_info_notification(info: str):
        if "notifications" in Config and Config["notifications"]:
            for dest, params in Config["notifications"].items():
                if not params["info"]:
                    continue

                if params["type"] == "slack":
                    if not SlackNotification.send_info_notification(params["url"], info):
                        logging.error(f"Failed to send info notification to Slack workspace \"{dest}\"")
                else:
                    logging.error(f"Attempted to send a site down notification to an unsupported notification type: {params['type']}")
