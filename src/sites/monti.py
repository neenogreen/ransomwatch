from datetime import datetime
import logging
import re
from bs4 import BeautifulSoup

from db.models import Victim
from net.proxy import Proxy
from .sitecrawler import SiteCrawler

class Monti(SiteCrawler):
    actor = "Monti"

    def _handle_page(self, body: str):
        soup = BeautifulSoup(body, "html.parser")
        victim_list = soup.find_all("div", class_="col-lg-4 col-sm-6 mb-4")

        for victim in victim_list:
            victim = victim.find("a")
            victim_name = victim.find("h5").text.strip()
            victim_leak_site = self.url + victim.attrs["href"]

            published = victim.find("div", class_="col-auto published").text.strip()
            published = datetime.strptime(published, "%Y-%m-%d %H:%M:%S")

            description = victim.find("div", class_="col-12").find("p").text.strip()

            q = self.session.query(Victim).filter_by(
                url=victim_leak_site, site=self.site)

            if q.count() == 0:
                # new victim
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
            r = p.get(f"{self.url}", headers=self.headers)
            self._handle_page(r.content.decode()) 
        self.site.last_scraped = datetime.utcnow()
