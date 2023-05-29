from datetime import datetime
import logging
import re
from bs4 import BeautifulSoup

from db.models import Victim
from net.proxy import Proxy
from .sitecrawler import SiteCrawler

class RansomwareBlog(SiteCrawler):
    actor = "RansomwareBlog"

    def _handle_page(self, body: str):
        soup = BeautifulSoup(body, "html.parser")
        victim_list = soup.find_all("article")

        for victim in victim_list:
            tmp = victim.find("h2").find("a")
            victim_name = tmp.text.strip()
            if "HOW TO BUY DATA?" in victim_name: continue
            victim_leak_site = tmp["href"]
            description = victim.find("div", class_="entry-content").get_text().strip()

            q = self.session.query(Victim).filter_by(
                url=victim_leak_site, site=self.site)

            if q.count() == 0:
                # new victim
                v = Victim(name=victim_name, url=victim_leak_site, published=datetime.utcnow(), description=description,
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
                r = p.get(f"{self.url}/?paged={i}", headers=self.headers)
                if "Nothing here" in r.content.decode():
                    break
                self._handle_page(r.content.decode()) 
                i = i + 1
        self.site.last_scraped = datetime.utcnow()
