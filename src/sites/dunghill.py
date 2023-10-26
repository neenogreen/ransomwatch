from datetime import datetime
import logging
import re
from bs4 import BeautifulSoup

from db.models import Victim
from net.proxy import Proxy
from .sitecrawler import SiteCrawler

class Dunghill(SiteCrawler):
    actor = "Dunghill"

    def _handle_page(self, body: str):
        soup = BeautifulSoup(body, "html.parser")
        victims = soup.find_all("div", class_="custom-container")

        for victim in victims:
            victim_name = victim.find("div", class_="ibody_title").text.strip()
            published = victim.find("div", class_="ibody_ft_left").find("p").text.strip()
            published_dt = datetime.strptime(published, "Date: %d.%m.%Y")
            description = victim.find("div", "ibody_body").get_text().strip()

            q = self.session.query(Victim).filter_by(
                name=victim_name, site=self.site)

            if q.count() == 0:
                # new victim
                v = Victim(name=victim_name, published=published_dt, description=description,
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
            r = p.get(f"{self.url}", headers=self.headers)
            self._handle_page(r.content.decode())
        self.site.last_scraped = datetime.utcnow()
