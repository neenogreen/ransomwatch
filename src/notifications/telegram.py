from datetime import datetime
import logging
import requests
from typing import Dict
import json
import telebot

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

        message = f"""\U00002623 *_RANSOMWATCH_* \U00002623 
*NEW VICTIM POSTED*
_Actor:_ {victim.site.actor}
_Organization:_ {victim.name}
_Published Date:_ {published_ts}
_First Seen:_ {datetime.strftime(victim.first_seen, '%b %d, %Y at %H:%M:%S UTC')}
_Description:_ {description}
_Victim Page:_ {victim.url if victim.url is not None else "no victim link available"}
_Victim Leak Site:_ {victim.site.url}
        """
        message = message.replace("-", "\-")
        message = message.replace("!", "\!")
        message = message.replace(".", "\.")
        message = message.replace("#", "\#")

        return telebot.TeleBot(token, parse_mode='MarkdownV2').send_message(chat_id, message)
