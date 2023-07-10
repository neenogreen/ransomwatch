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
        victim_list = soup.find_all("article")

        for victim in victim_list:
            tmp = victim.find("h2")
            victim_name = tmp.get_text().strip()
            victim_leak_site = self.url + tmp.find("a")["href"]

            q = self.session.query(Victim).filter_by(name=victim_name,
                url=victim_leak_site, site=self.site)

            if q.count() == 0:
                # new victim
                published = datetime.strptime(victim.find("span", class_="post-meta").find("time")["datetime"], "%d-%m-%Y")
                description = victim.find("p", class_="post-excerpt").get_text().strip()
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
            page = 1
            while True:
                r = p.get(f"{self.url}/page/{page}", headers=self.headers)
                if r.status_code == 404:
                    break
                self._handle_page(r.content.decode()) 
                page += 1
        self.site.last_scraped = datetime.utcnow()
