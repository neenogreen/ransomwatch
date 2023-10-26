from datetime import datetime
import logging
import re
from bs4 import BeautifulSoup

from db.models import Victim
from net.proxy import Proxy
from .sitecrawler import SiteCrawler

class FreeCivilian(SiteCrawler):
    actor = "Free Civilian"

    def scrape_new_leaks(self, body: str):
        soup = BeautifulSoup(body, "html.parser")
        victim_list = soup.find_all("a", class_="more")[:-1]

        for victim in victim_list:
            victim_name = victim.attrs["href"] 
            if "kyivcity" in victim_name:
                continue

            q = self.session.query(Victim).filter_by(
                name=victim_name, site=self.site)

            if q.count() == 0:
                v = Victim(name=victim_name, published=datetime.utcnow(),
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

    def _handle_page(self, body: str):
        soup = BeautifulSoup(body, "html.parser")
        victim_list = soup.find("section", attrs={"id": "openSource"}).find_all("li")[:-1]

        for victim in victim_list:
            try:
                victim_name = victim.find("a").get_text().strip().split(" - ")[0]
            except:
                continue

            q = self.session.query(Victim).filter_by(
                name=victim_name, site=self.site)

            if q.count() == 0:
                # new victim
                try:
                    description = victim.find("ul").get_text().strip()
                except:
                    continue
                v = Victim(name=victim_name, published=datetime.utcnow(),
                            first_seen=datetime.utcnow(), last_seen=datetime.utcnow(), site=self.site,
                            description=description)
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
            r = p.get(f"{self.url}/new_leaks.html", headers=self.headers)
            self.scrape_new_leaks(r.content.decode()) 

            r = p.get(f"{self.url}", headers=self.headers)
            self._handle_page(r.content.decode())

        self.site.last_scraped = datetime.utcnow()
