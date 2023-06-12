from datetime import datetime
import logging
import re
from bs4 import BeautifulSoup
import urllib.parse
import json

from db.models import Victim
from net.proxy import Proxy
from .sitecrawler import SiteCrawler

class BlackSuit(SiteCrawler):
    actor = "BlackSuit"

    def _handle_page(self, body: str):
        soup = BeautifulSoup(body, "html.parser")
        for victim in soup.find_all("div", class_="card"):
            tmp = victim.find("div", class_="title")
            victim_url = self.url + tmp.find("a")["href"]
            victim_name = tmp.get_text()
            tmp = victim.find("div", class_="url")
            description = tmp.get_text() + ": " + tmp.find("a")["href"] + "\n"
            description += victim.find("div", class_="text").get_text() + "\n"
            try:
                for link in victim.find("div", class_="links").find_all("a"):
                    description += link.text.strip() + ": " + link["href"] + "\n"
            except:
                pass
            
            q = self.session.query(Victim).filter_by(
                name=victim_name, url=victim_url, site=self.site)

            if q.count() == 0:
                # new victim
                v = Victim(name=victim_name, published=datetime.utcnow(), description=description, first_seen=datetime.utcnow(), last_seen=datetime.utcnow(), site=self.site, url=victim_url)
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
                r = p.get(f"{self.url}/?page={i}", headers=self.headers).content.decode()
                if 'Not found' in r:
                    break
                self._handle_page(r)
                i = i + 1
        self.site.last_scraped = datetime.utcnow()
