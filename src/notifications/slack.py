from datetime import datetime
import logging
import requests
from typing import Dict
import json

from db.models import Site, Victim
from .source import NotificationSource

class SlackNotification(NotificationSource):
    def _post_webhook(body: Dict, url: str) -> bool:
        r = requests.post(url, json=body)
        if r.status_code != 200:
            logging.error(
                f"Error sending Slack notification ({r.status_code}): {r.content.decode()}")
            return False

        return True

    def send_new_victim_notification(url: str, victim: Victim) -> bool:
        published_ts = datetime.strftime(victim.published, '%b %d, %Y') if victim.published is not None else "N/A"
        if victim.description:
            description = victim.description
        else:
            description = " " 
        if len(description) > 1000:
            description = description[:1000] + "..."

        body = {
            "attachments": [
                {
                    "color": "#03a1fc",
                    "blocks": [
                        {
                            "type": "header",
                            "text": {
                                "type": "plain_text",
                                "text": "New Victim Posted"
                            }
                        },
                        {
                            "type": "section",
                            "fields": [
                                {
                                    "type": "mrkdwn",
                                    "text": f"*Actor:*\n{victim.site.actor}"
                                },
                                {
                                    "type": "mrkdwn",
                                    "text": f"*Organization:*\n{victim.name}"
                                },
                                {
                                    "type": "mrkdwn",
                                    "text": f"*Published Date:*\n{published_ts}"
                                },
                                {
                                    "type": "mrkdwn",
                                    "text": f"*First Seen:*\n{datetime.strftime(victim.first_seen, '%b %d, %Y at %H:%M:%S UTC')}" if victim.first_seen is not None else "*First Seen:*\nNone"
                                },
                                {
                                    "type": "mrkdwn",
                                    "text": f"*Description:*\n{description}"
                                }
                            ]
                        },
                        {
                            "type": "section",
                            "fields": [
                                {
                                    "type": "mrkdwn",
                                    "text": f"<{victim.url}|View Victim Page>" if victim.url is not None else "(no victim link available)"
                                },
                                {
                                    "type": "mrkdwn",
                                    "text": f"<{victim.site.url}|View Leak Site>"
                                }
                            ]
                        }
                    ]
                }
            ]
        }

        return SlackNotification._post_webhook(body, url)

    def send_victim_removed_notification(url: str, victim: Victim) -> bool:
        published_ts = datetime.strftime(victim.published, '%b %d, %Y') if victim.published is not None else "N/A"

        body = {
            "attachments": [
                {
                    "color": "#f5ad27",
                    "blocks": [
                        {
                            "type": "header",
                            "text": {
                                "type": "plain_text",
                                "text": "Victim Removed"
                            }
                        },
                        {
                            "type": "section",
                            "fields": [
                                {
                                    "type": "mrkdwn",
                                    "text": f"*Actor:*\n{victim.site.actor}"
                                },
                                {
                                    "type": "mrkdwn",
                                    "text": f"*Organization:*\n{victim.name}"
                                },
                                {
                                    "type": "mrkdwn",
                                    "text": f"*Date Originally Published:*\n{published_ts}"
                                },
                                {
                                    "type": "mrkdwn",
                                    "text": f"*Last Seen:*\n{datetime.strftime(victim.last_seen, '%b %d, %Y at %H:%M:%S UTC')}"
                                }
                            ]
                        },
                        {
                            "type": "section",
                            "fields": [
                                {
                                    "type": "mrkdwn",
                                    "text": f"<{victim.site.url}|View Leak Site>"
                                }
                            ]
                        }
                    ]
                }
            ]
        }

        return SlackNotification._post_webhook(body, url)

    def send_site_down_notification(url: str, site: Site) -> bool:
        last_up_ts = datetime.strftime(site.last_up, '%b %d, %Y at %H:%M:%S UTC') if site.last_up is not None else "N/A"
        diff = (datetime.utcnow() - site.last_up).total_seconds() / 3600 if site.last_up is not None else 0

        body = {
            "attachments": [
                {
                    # If the dls is down for at least 5 hours change the severity of the slack alert
                    "color": "#fcc203" if diff < 5  else "#ff7518",
                    "blocks": [
                        {
                            "type": "header",
                            "text": {
                                "type": "plain_text",
                                "text": "Site Down"
                            }
                        },
                        {
                            "type": "section",
                            "fields": [
                                {
                                    "type": "mrkdwn",
                                    "text": f"*Actor:*\n{site.actor}"
                                },
                                {
                                    "type": "mrkdwn",
                                    "text": f"*Last Up:*\n{last_up_ts}"
                                }
                            ]
                        },
                        {
                            "type": "section",
                            "fields": [
                                {
                                    "type": "mrkdwn",
                                    "text": f"<{site.url}|View Leak Site>"
                                }
                            ]
                        }
                    ]
                }
            ]
        }

        return SlackNotification._post_webhook(body, url)

    def send_error_notification(url: str, context: str, error: str, fatal: bool = False) -> bool:

        if error:
            err = error
        else:
            err = " "
        if len(err) > 1000:
            err = err[:1000] + "..."

        body = {
            "attachments": [
                {
                    "color": "#fc0303",
                    "blocks": [
                        {
                            "type": "header",
                            "text": {
                                "type": "plain_text",
                                "text": f"{'Fatal ' if fatal else ''}Error"
                            }
                        },
                        {
                            "type": "section",
                            "text": {
                                "type": "mrkdwn",
                                "text": f"*An error occurred:* {context}"
                            }
                        },
                        {
                            "type": "section",
                            "text": {
                                "type": "mrkdwn",
                                "text": f"```{err}```\nFor more details, please check the app container logs"
                            }
                        },
                        {
                            "type": "context",
                            "elements": [
                                {
                                    "type": "mrkdwn",
                                    "text": "If you think this is a bug, please <https://github.com/neenogreen/ransomwatch/issues|open an issue> on GitHub"
                                }
                            ]
                        }
                    ]
                }
            ]
        }

        return SlackNotification._post_webhook(body, url)
    
    def send_info_notification(url: str, info: str) -> bool:
        body = {
            "attachments": [
                {
                    "color": "#0FFF50",
                    "blocks": [
                        {
                            "type": "header",
                            "text": {
                                "type": "plain_text",
                                "text": f"Info"
                            }
                        },
                        {
                            "type": "section",
                            "text": {
                                "type": "mrkdwn",
                                "text": info
                            }
                        }
                    ]
                }
            ]
        }

        return SlackNotification._post_webhook(body, url)
