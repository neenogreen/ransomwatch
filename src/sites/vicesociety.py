from datetime import datetime
import logging

from bs4 import BeautifulSoup

from db.models import Victim
from net.proxy import Proxy
from .sitecrawler import SiteCrawler


class ViceSociety(SiteCrawler):
    actor = "ViceSociety"

    def scrape_victims(self):
        with Proxy() as p:
            r = p.get(f"{self.url}", headers=self.headers)

            soup = BeautifulSoup(r.content.decode(), "html.parser")

            victim_list = soup.find("table").find_all("table")[1].find_all("tr")
            for victim in victim_list:
                if "View documents" not in victim.text.strip():
                    continue
                victim_name = victim.find("font", {"size": 4}).text.strip()
                
                victim_leak_site = victim.find_all("a")[1].attrs["href"]
                 
                q = self.session.query(Victim).filter_by(
                    url=victim_leak_site, site=self.site)

                if q.count() == 0:
                    # new victim
                    description = ""
                    text = victim.find_all("font", {"size": 2})
                    for e in text:
                        description += e.text.strip()
                        description += "\n"
                    
                    v = Victim(name=victim_name, url=victim_leak_site,
                            description=description,
                            published=datetime.utcnow(),
                            first_seen=datetime.utcnow(),
                            last_seen=datetime.utcnow(), site=self.site)
                    self.session.add(v)
                    self.new_victims.append(v)
                else:
                    # already seen, update last_seen
                    v = q.first()
                    v.last_seen = datetime.utcnow()

                # add the org to our seen list
                self.current_victims.append(v)
            self.session.commit()

        self.site.last_scraped = datetime.utcnow()

        # just for good measure
        self.session.commit()
