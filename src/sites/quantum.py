from datetime import datetime
import logging

from bs4 import BeautifulSoup

from db.models import Victim
from net.proxy import Proxy
from .sitecrawler import SiteCrawler


class Quantum(SiteCrawler):
    actor = "Quantum"

    def scrape_victims(self):
        with Proxy() as p:
            r = p.get(f"{self.url}", headers=self.headers)

            soup = BeautifulSoup(r.content.decode(), "html.parser")

            victim_list = soup.find_all("div", class_="panel-body")

            for victim in victim_list:
                victim_name = victim.find("h2", class_="blog-post-title").text.strip()
                victim_leak_site = self.url + victim.find("a").attrs["href"]

                q = self.session.query(Victim).filter_by(
                    url=victim_leak_site, site=self.site)

                if q.count() == 0:
                    # new victim
                    published = datetime.strptime(victim.find("p", class_="blog-post-date pull-right").text.strip(), "%Y-%m-%d")
                    description = victim.find("p", attrs={"class": None}).text.strip()

                    v = Victim(name=victim_name, url=victim_leak_site, published=published, first_seen=datetime.utcnow(), last_seen=datetime.utcnow(), site=self.site, description=description)
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
