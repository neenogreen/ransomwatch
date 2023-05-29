from datetime import datetime
import logging
import re
from bs4 import BeautifulSoup

from db.models import Victim
from net.proxy import Proxy
from .sitecrawler import SiteCrawler

class Dunghill(SiteCrawler):
    actor = "Dunghill"

    def _handle_page(self, body: str):
        soup = BeautifulSoup(body, "html.parser")

        victim_name = soup.find("div", class_="block-heading pt-4 mt-5").text.strip()
        published = soup.find("div", class_="block__details-count cur_date_block").text.strip().replace("a.m.", "AM").replace("p.m.", "PM")
        published_dt = datetime.strptime(published, "%B %d, %Y, %I:%M %p")
        description = re.sub('PREVIOUS LOT:.*\n', '', soup.get_text().strip()) # remove noise
        description = re.sub(r'\n+', '', description) # remove newlines

        q = self.session.query(Victim).filter_by(
            name=victim_name, site=self.site)

        if q.count() == 0:
            # new victim
            v = Victim(name=victim_name, published=published_dt, description=description,
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
                if i == 1:
                    r = p.get(f"{self.url}", headers=self.headers)
                else:
                    r = p.get(f"{self.url}/index{i}.html", headers=self.headers)
                if r.status_code == 404:
                    break
                self._handle_page(r.content.decode())
                i = i + 1
        self.site.last_scraped = datetime.utcnow()
