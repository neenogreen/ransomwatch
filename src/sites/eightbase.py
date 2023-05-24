from datetime import datetime
import logging
import re
from bs4 import BeautifulSoup

from db.models import Victim
from net.proxy import Proxy
from .sitecrawler import SiteCrawler

class Eightbase(SiteCrawler):
    actor = "8base"

    def _handle_page(self, body: str):
        soup = BeautifulSoup(body, "html.parser")
        victim_list = soup.find_all("div", class_="list-group-item rounded-3 py-3 bg-body-secondary text-bg-dark mb-2 position-relative")

        for victim in victim_list:
            link_and_name = victim.find("a", class_="stretched-link")
            victim_name = link_and_name.text.strip()
            victim_leak_site = link_and_name["href"]
            published = victim.find("div", class_="d-flex gap-2 small mt-1 opacity-25").find_all("div")[1].text.strip()
            published = datetime.strptime(published, "Publish: %d.%m.%Y")
            description = ""
            for desc in victim.find_all("div", class_="small opacity-50"):
                description += desc.text.strip() + "\n"

            q = self.session.query(Victim).filter_by(name=victim_name,
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
