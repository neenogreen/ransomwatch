from datetime import datetime
import logging
import re
from bs4 import BeautifulSoup

from db.models import Victim
from net.proxy import Proxy
from .sitecrawler import SiteCrawler

class RaGroup(SiteCrawler):
    actor = "Ra Group"

    def _handle_page(self, body: str):
        soup = BeautifulSoup(body, "html.parser")
        victim_name = re.split("\(([^\)]+)\)", soup.find("h1").text.strip())[0].strip()
        victim_leak_site = soup.find("meta", property="og:url")["content"]
        description = soup.find("div", class_="post-content markdown-body").get_text()
        published = datetime.strptime(soup.find("time", class_="post-date")["datetime"], "%Y-%m-%d %H:%M:%S PDT")

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
            soup = BeautifulSoup(r.content.decode(), "html.parser")
            for e in soup.find_all("div", class_="col-xs-11 col-sm-10"):
                r = p.get(self.url + e.find("a")["href"], headers=self.headers)
                self._handle_page(r.content.decode()) 
        self.site.last_scraped = datetime.utcnow()
