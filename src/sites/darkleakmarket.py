from datetime import datetime
import logging

from bs4 import BeautifulSoup

from db.models import Victim
from net.proxy import Proxy
from .sitecrawler import SiteCrawler


class DarkLeakMarket(SiteCrawler):
    actor = "DarkLeakMarket"

    def scrape_victims(self):
        with Proxy() as p:
            r = p.get(f"{self.url}", headers=self.headers)

            soup = BeautifulSoup(r.content.decode(), "html.parser")

            victim_list = soup.find_all("td")

            for victim in victim_list:
                victim_parsed = victim.find_all("a")[1]
                victim_name = victim_parsed.get_text()

                victim_leak_site = self.url + "/" + victim_parsed.attrs["href"]

                q = self.session.query(Victim).filter_by(
                    url=victim_leak_site, site=self.site)

                if q.count() == 0:
                    # new victim
                    r = p.get(victim_leak_site, headers=self.headers)
                    soup1 = BeautifulSoup(r.content.decode(), "html.parser")
                    tmp = soup1.find_all("div", class_="card-body")
                    description = tmp[0].get_text()
                    tmp = tmp[1].find_all("h4")
                    description += tmp[0].get_text() + "$\n"
                    description += tmp[1].get_text() + "bitcoin"

                    v = Victim(name=victim_name, url=victim_leak_site, published=datetime.utcnow(), first_seen=datetime.utcnow(), last_seen=datetime.utcnow(), site=self.site, description=description)
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
