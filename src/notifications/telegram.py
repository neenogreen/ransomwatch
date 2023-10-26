from datetime import datetime
import logging
import requests
from typing import Dict
import json
import telebot
import time

from db.models import Site, Victim
from .source import NotificationSource

class TelegramNotification(NotificationSource):

    def send_new_victim_notification(token: str, chat_id: str, victim: Victim) -> bool:
        published_ts = datetime.strftime(victim.published, '%b %d, %Y') if victim.published is not None else "N/A"
        if victim.description:
            description = victim.description
        else:
            description = " " 
        if len(description) > 1000:
            description = description[:1000] + "..."

        message = f"""\U00002623 RANSOMWATCH \U00002623 
NEW VICTIM POSTED
Actor: {victim.site.actor}
Organization: {victim.name}
Published Date: {published_ts}
First Seen: {datetime.strftime(victim.first_seen, '%b %d, %Y at %H:%M:%S UTC')}
Description: {description}
Victim Page: {victim.url if victim.url is not None else "no victim link available"}
Victim Leak Site: {victim.site.url}
        """

        # Max 20 messages per minute to the same group
        time.sleep(4)

        return telebot.TeleBot(token).send_message(chat_id, message)
