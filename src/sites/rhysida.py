from datetime import datetime
import logging
import re
from bs4 import BeautifulSoup
import html2text

from db.models import Victim
from net.proxy import Proxy
from .sitecrawler import SiteCrawler

class Rhysida(SiteCrawler):
    actor = "Rhysida"

    def _handle_page(self, body: str):
        soup = BeautifulSoup(body, "html.parser")
        victim_list = soup.find_all("div", class_="border m-2 p-2")

        for victim in victim_list:
            victim_name = victim.find("div", class_="m-2 h4").find("a").text.strip()
            victim_desc = html2text.html2text(victim.find("div", class_="m-2").text.strip())
            try:
                victim_leak_site = victim.find("div", class_="m-2").find("p").find("a")["href"]
            except:
                victim_leak_site = victim.find("div", class_="m-2").find("a")["href"]
            published_dt = datetime.utcnow()

            q = self.session.query(Victim).filter_by(
                name=victim_name, site=self.site)

            if q.count() == 0:
                # new victim
                v = Victim(name=victim_name, url=victim_leak_site, published=published_dt,
                            first_seen=datetime.utcnow(), last_seen=datetime.utcnow(), site=self.site, description=victim_desc)
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
            r = p.get(f"{self.url}/archive.php", headers=self.headers)
            self._handle_page(r.content.decode()) 
        self.site.last_scraped = datetime.utcnow()
