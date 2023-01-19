from datetime import datetime
import logging

from config import Config
from db.models import Victim
from net.proxy import Proxy
from .sitecrawler import SiteCrawler

import json
from bs4 import BeautifulSoup

from notifications.manager import NotificationManager

class RansomHouse(SiteCrawler):
    actor = "RansomHouse"

    def scrape_victims(self):
        with Proxy() as p:
            r = p.get(self.url + "/a")
        victim_list = json.loads(r.content.decode())
        victim_list = victim_list["data"]

        for victim in victim_list:
            victim_name = victim["header"]
            victim_leak_site = self.url + "/r/" + victim["id"]

            q = self.session.query(Victim).filter_by(
                    site=self.site, url=victim_leak_site)

            if q.count() == 0:
                victim_description = "Website: " + victim["url"] + "\n"
                victim_description += "Revenue: " + victim["revenue"] + "\n"
                victim_description += "Employees: " + victim["employees"] + "\n"
                victim_description += "Leak size: " + victim["volume"] + "\n"
                victim_description += victim["info"]
                with Proxy() as p:
                    r = p.get(self.url + "/a/" + victim["id"])
                tmp = json.loads(r.content.decode())["data"]["content"]
                victim_description += BeautifulSoup(tmp, "lxml").get_text()

                if "*" in victim["actionDate"]:
                    published_dt = datetime.utcnow()
                else:
                    published_dt = datetime.strptime(victim["actionDate"], "%d/%m/%Y")
                v = Victim(name=victim_name, description=victim_description, url=victim_leak_site, published=published_dt, first_seen=datetime.utcnow(), last_seen=datetime.utcnow(), site=self.site)
                self.session.add(v)
                self.new_victims.append(v)
            else:
                v = q.first()
                v.last_seen = datetime.utcnow()

            self.current_victims.append(v)
        self.session.commit()
        self.site.last_scraped = datetime.utcnow()

