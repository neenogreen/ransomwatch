from datetime import datetime
import logging
import re
from bs4 import BeautifulSoup

from db.models import Victim
from net.proxy import Proxy
from .sitecrawler import SiteCrawler

class Donut(SiteCrawler):
    actor = "Donut"

    def _handle_page(self, body: str):
        soup = BeautifulSoup(body, "html.parser")
        victim_list = soup.find_all("tr")[1:-1]

        for victim in victim_list:
            elems = victim.find_all("td")
            victim_name = elems[0].text.strip()
            if "index.php" in victim_name: continue
            victim_leak_site = elems[3].find("a")["href"]

            q = self.session.query(Victim).filter_by(name=victim_name,
                url=victim_leak_site, site=self.site)

            if q.count() == 0:
                # new victim
                v = Victim(name=victim_name, url=victim_leak_site, published=datetime.utcnow(),
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
