from datetime import datetime
import logging

from config import Config
from db.models import Victim
from net.proxy import Proxy
from .sitecrawler import SiteCrawler

import json
from bs4 import BeautifulSoup

from notifications.manager import NotificationManager

class Royal(SiteCrawler):
    actor = "Royal"

    def __init__(self, url: str):
        super(Royal, self).__init__(url)

        self.headers["Accept"] = "*/*"
        self.headers["Origin"] = url
    
    def is_site_up(self) -> bool:
        with Proxy() as p:
            try:
                r = p.get(f"{self.url}/api/posts/list", headers=self.headers, timeout=Config["timeout"])

                if r.status_code >= 400:
                    return False
            except Exception as e:
                print(e)
                return False

        self.site.last_up = datetime.utcnow()

        return True

    def find_occurrences(self, s, ch):
        return [i for i, letter in enumerate(s) if letter == ch]

    def _handle_page(self, body: str):
        victim_list = json.loads(body)
        victim_list = victim_list["data"]

        for victim in victim_list:
            victim_name = victim["title"]
            victim_links = victim["links"]
            if len(victim_links) == 0:
                victim_leak_site = victim["id"]
            elif len(victim_links) == 1:
                victim_leak_site = victim_links[0]
            else:
                try:
                    victim_leak_site = victim_links[0].split("|")[1]
                    tmp = self.find_occurrences(victim_leak_site, "/")
                    tmp = tmp[-1]
                    victim_leak_site = victim_leak_site[:tmp]
                except:
                    victim_leak_site = victim_links[0]
            victim_description = BeautifulSoup(victim["text"], "lxml").text + "\n"
            victim_description += "Website: " + victim["url"] + "\n"
            victim_description += "Revenue: " + victim["revenue"] + "\n"
            victim_description += "Employees: " + victim["employees"] + "\n"
            victim_description += "Leak size: " + victim["size"]

            q = self.session.query(Victim).filter_by(
                    site=self.site, name=victim_name)

            if q.count() == 0:
                published_dt = datetime.strptime(victim["time"], "%Y-%B-%d")
                v = Victim(name=victim_name, description=victim_description, url=victim_leak_site, published=published_dt, first_seen=datetime.utcnow(), last_seen=datetime.utcnow(), site=self.site)
                self.session.add(v)
                self.new_victims.append(v)
            else:
                v = q.first()
                v.last_seen = datetime.utcnow()
                if v.url != victim_leak_site:
                    v.url = victim_leak_site
                    NotificationManager.send_new_victim_notification(v)

            self.current_victims.append(v)
        self.session.commit()

    def scrape_victims(self):
        page = 1
        with Proxy() as p:
            while True:
                try:
                    r = p.post(self.url + "/api/posts/list", headers=self.headers, json={"page": page})
                    if "\"data\":[]" in r.text:
                        break
                    self._handle_page(r.content.decode())
                    page += 1
                except Exception as e:
                    print(e)
                    break
        self.site.last_scraped = datetime.utcnow()
