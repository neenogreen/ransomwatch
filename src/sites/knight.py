from datetime import datetime
import logging
import re
from bs4 import BeautifulSoup

from db.models import Victim
from net.proxy import Proxy
from .sitecrawler import SiteCrawler

class Knight(SiteCrawler):
    actor = "Knight"

    def _handle_page(self, body: str):
        soup = BeautifulSoup(body, "html.parser")
        victim_list = soup.find_all("div", class_="col-sm-6 col-lg-4")

        for victim in victim_list:
            victim_name = victim.find("h2", class_="card-title").text.strip()
            published = datetime.strptime(victim.find("div", class_="d-flex justify-content-between align-items-center mb-4").text.strip().split("\n")[2], "%Y-%m-%d")
            description = victim.find("p", class_="card-text blog-content-truncate").get_text().strip()
            victim_leak_site = self.url + victim.find("div", class_="card-footer text-muted").find("a")["href"]

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
        self.init_scrape = True
        page = 1
        while True:
            with Proxy() as p:
                r = p.get(f"{self.url}/?page={page}", headers=self.headers)
                self._handle_page(r.content.decode()) 
                page += 1
                soup = BeautifulSoup(r.content.decode(), "html.parser")
                if not soup.find("li", class_="page-item next"): break
        self.site.last_scraped = datetime.utcnow()
