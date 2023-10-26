from datetime import datetime
import logging
import html2text

from db.models import Victim
from net.proxy import Proxy
from .sitecrawler import SiteCrawler

class Trigona(SiteCrawler):
    actor = "Trigona"

    def _handle_page(self, body: str):
        victim_list = body["data"]["leaks"]

        for victim in victim_list:
            victim_name = victim["title"].strip()
            victim_leak_site = victim["link"].strip()

            q = self.session.query(Victim).filter_by(
                url=victim_leak_site, site=self.site)

            if q.count() == 0:
                # new victim
                description = html2text.html2text(victim["descryption"])
                published = datetime.strptime(victim["created_at"].split(".")[0], "%Y-%m-%dT%H:%M:%S")
                v = Victim(name=victim_name, url=victim_leak_site, published=published, description=description,
                            first_seen=datetime.utcnow(), last_seen=datetime.utcnow(), site=self.site)
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
            i = 1
            while True:
                r = p.get(f"{self.url}/api?page={i}", headers=self.headers).json()
                if not r["data"]["leaks"]: break
                self._handle_page(r)
                i = i + 1
        self.site.last_scraped = datetime.utcnow()
