from datetime import datetime
import logging

from bs4 import BeautifulSoup

from db.models import Victim
from net.proxy import Proxy
from .sitecrawler import SiteCrawler


class Daixin(SiteCrawler):
    actor = "Daixin"

    def scrape_victims(self):
        with Proxy() as p:
            r = p.get(f"{self.url}", headers=self.headers)

            soup = BeautifulSoup(r.content.decode(), "html.parser")

            # get max page number
            victim_list = soup.find("main").find_all("div")

            for victim in victim_list:
                victim_name = victim.find("h4").text.strip()

                q = self.session.query(Victim).filter_by(
                    name=victim_name, site=self.site)

                if q.count() == 0:
                    # new victim
                    tmp = victim.find("h6")
                    description = tmp.text.strip() + "\n"
                    tmp = victim.find_all("p")
                    for e in tmp:
                        description += e.get_text().strip() + "\n"
                    tmp = victim.find_all("h6")[1:]
                    for e in tmp:
                        tmp1 = e.find("a")
                        description += e.text.strip() + " - " + tmp1.attrs["href"] + "\n"
                    v = Victim(name=victim_name, published=datetime.utcnow(),
                               first_seen=datetime.utcnow(), last_seen=datetime.utcnow(), site=self.site,
                               description=description)
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
