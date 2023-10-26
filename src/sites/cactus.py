from datetime import datetime
import logging
import re
from bs4 import BeautifulSoup

from db.models import Victim
from net.proxy import Proxy
from .sitecrawler import SiteCrawler

class Cactus(SiteCrawler):
    actor = "Cactus"

    def is_site_up(self) -> bool:
        with Proxy() as p:
            try:
                r = p.get(self.url, verify=False)
                if r.status_code >= 400:
                    return False
            except Exception as e:
                return False
        self.site.last_up = datetime.utcnow()           
        return True

    def _handle_page(self, body: str):
        soup = BeautifulSoup(body, "html.parser")

        victims = soup.find_all("article")

        for victim in victims:
            victim_name = victim.find("h2").text.strip()
            published = victim.find("div", class_="text-[12px] leading-tight").text.strip()
            published_dt = datetime.strptime(published, "%B %d, %Y")
            victim_url = self.url + victim.find("a", class_="before:absolute before:inset-0")["href"]
            description = victim.find("p").text.strip()

            q = self.session.query(Victim).filter_by(
                name=victim_name, url=victim_url, site=self.site)

            if q.count() == 0:
                # new victim
                v = Victim(name=victim_name, published=published_dt, description=description, url=victim_url,
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
                r = p.get(f"{self.url}/?page={i}", headers=self.headers, verify=False)
                if "Nothing was found" in r.text:
                    break
                self._handle_page(r.content.decode())
                i = i + 1
        self.site.last_scraped = datetime.utcnow()
