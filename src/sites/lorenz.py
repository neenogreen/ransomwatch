from datetime import datetime
import logging
import re
from bs4 import BeautifulSoup

from db.models import Victim
from net.proxy import Proxy
from .sitecrawler import SiteCrawler

class Lorenz(SiteCrawler):
    actor = "Lorenz"

    def _handle_page(self, body: str):
        soup = BeautifulSoup(body, "html.parser")
        victim_list = soup.find_all("div", class_="panel panel-primary")

        for victim in victim_list:
            victim_name = victim.find("div", class_="panel-heading").find("h3").text.strip()
            victim_leak_site = self.url + "/#" + victim.get("id")

            if victim.find("span", class_="glyphicon"):
                published = victim.find("span", class_="glyphicon").next_sibling
                published = published.lstrip()
                try:
                    published_dt = datetime.strptime(published, "Posted %b %d, %Y.")
                except:
                    published_dt = datetime.strptime(published.split("U")[0], "Posted %b %d, %Y ")
            else:
                published_dt = datetime.utcnow()

            q = self.session.query(Victim).filter_by(
                url=victim_leak_site, site=self.site)

            if q.count() == 0:
                # new victim
                v = Victim(name=victim_name, url=victim_leak_site, published=published_dt,
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
