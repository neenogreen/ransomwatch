from datetime import datetime
import logging
import re
from bs4 import BeautifulSoup

from db.models import Victim
from net.proxy import Proxy
from .sitecrawler import SiteCrawler

class Vendetta(SiteCrawler):
    actor = "Vendetta"

    def _handle_page(self, body: str):
        soup = BeautifulSoup(body, "html.parser")
        victim_list = soup.find_all("div", class_="post")

        for victim in victim_list:
            victim_leak_site = self.url + victim.find("a")["href"]

            q = self.session.query(Victim).filter_by(
                url=victim_leak_site, site=self.site)

            if q.count() == 0:
                # new victim
                with Proxy() as p:
                    r = p.get(victim_leak_site, headers=self.headers)
                victim = BeautifulSoup(r.content.decode(), "html.parser").find("div", class_="post").find("div")
                description = victim.get_text()
                victim_name = victim.find("h2").text.strip()
                published_dt = datetime.strptime(re.search(r'(.*(?:Date the files were received).*)', description).group(1).strip().split(":")[1].strip(), "%d %B %Y")
                v = Victim(name=victim_name, url=victim_leak_site, published=published_dt, description=description,
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
