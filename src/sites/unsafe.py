from datetime import datetime
import logging
from config import Config

import json
from bs4 import BeautifulSoup

from db.models import Victim
from net.proxy import Proxy
from .sitecrawler import SiteCrawler


class Unsafe(SiteCrawler):
    actor = "Unsafe"

    def _handle_page(self, body: str):
        victim_list = json.loads(body)

        for victim in victim_list:
            victim_name = victim["title"]
            if victim["files"]:
                victim_leak_site = victim["files"].split(";")[0]
            else:
                victim_leak_site = self.url + "#" + victim_name
            victim_description = BeautifulSoup(victim["content"], "lxml").get_text().strip() + "\nCountry: " + victim["country"] + "\nWebsite: " + victim["website"]
            
            q = self.session.query(Victim).filter_by(
                url=victim_leak_site, site=self.site, name=victim_name)

            if q.count() == 0:
                # new victim
                published_dt = datetime.strptime(victim["disclosed_at"], "%Y-%m-%dT%H:%M:%SZ")
                v = Victim(name=victim_name, description=victim_description, url=victim_leak_site, published=published_dt, first_seen=datetime.utcnow(), last_seen=datetime.utcnow(), site=self.site)
                self.session.add(v)
                self.new_victims.append(v)
            else:
                # already seen, update last_seen
                v = q.first()
                v.last_seen = datetime.utcnow()

            # add the org to our seen list
            self.current_victims.append(v)
        self.session.commit()

    def scrape_victims(self):
        page = 0
        with Proxy() as p:
            while True:
                r = p.get(f"{self.url}/api/posts?page={str(page)}", headers=self.headers)
                if len(r.text) < 10:
                    break
                self._handle_page(r.content.decode())
                page += 1
        self.site.last_scraped = datetime.utcnow()
