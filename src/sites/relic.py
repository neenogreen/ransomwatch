from datetime import datetime
import logging

from bs4 import BeautifulSoup

from db.models import Victim
from net.proxy import Proxy
from .sitecrawler import SiteCrawler


class Relic(SiteCrawler):
    actor = "Relic"

    def scrape_victims(self):
        with Proxy() as p:
            r = p.get(f"{self.url}", headers=self.headers)

            soup = BeautifulSoup(r.content.decode(), "html.parser")

            # get max page number
            victim_list = soup.find_all("div", class_="content")

            for victim in victim_list:
                victim_name = victim.find("div", class_="name").text.strip()

                victim_leak_site = self.url + victim.find("div", class_="leak").find("a").attrs["href"]

                q = self.session.query(Victim).filter_by(
                    url=victim_leak_site, site=self.site)

                if q.count() == 0:
                    # new victim
                    tmp = victim.find("div", class_="card row")
                    description = tmp.find("div", class_="description").text.strip() + "\n"
                    description += "Website: " + tmp.find("div", class_="website").get_text().strip() + "\n"
                    description += "Address: " + tmp.find("div", class_="addr column").get_text().strip() + "\n"
                    description += "Phones: " + tmp.find("div", class_="phones").get_text().strip() + "\n"
                    description += "Revenue: " + tmp.find("div", class_="revenue").get_text().strip()
                    v = Victim(name=victim_name, url=victim_leak_site, published=datetime.utcnow(),
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
