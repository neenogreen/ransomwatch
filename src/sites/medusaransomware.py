from datetime import datetime
import logging
import re
from bs4 import BeautifulSoup
import urllib.parse
import json

from db.models import Victim
from net.proxy import Proxy
from .sitecrawler import SiteCrawler

class MedusaRansomware(SiteCrawler):
    actor = "MedusaRansomware"

    def _handle_page(self, body: str):
        for victim in json.loads(body)["list"]:
            published = datetime.strptime(victim["deadline"], "%Y-%m-%d %H:%M:%S")
            description = victim["description"]
            victim_url = self.url + "/detail?id=" + victim["id"]
            victim_name = victim["company_name"]
            
            q = self.session.query(Victim).filter_by(
                name=victim_name, url=victim_url, site=self.site)

            if q.count() == 0:
                # new victim
                v = Victim(name=victim_name, published=published, description=description, first_seen=datetime.utcnow(), last_seen=datetime.utcnow(), site=self.site, url=victim_url)
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
        with Proxy() as p:
            i = 0
            while True:
                r = p.get(f"{self.url}/api/search?company=&page={i}", headers=self.headers).text.strip()
                self._handle_page(r)
                i = i + 1
                if '"end":true' in r:
                    break
        self.site.last_scraped = datetime.utcnow()
