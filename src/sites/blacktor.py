from datetime import datetime
import logging

from bs4 import BeautifulSoup

from db.models import Victim
from net.proxy import Proxy
from .sitecrawler import SiteCrawler


class Blacktor(SiteCrawler):
    actor = "Blacktor"

    def scrape_victims(self):
        with Proxy() as p:
            r = p.get(f"{self.url}/0x00/data-breach.html", headers=self.headers,
                    auth=("bl@ckt0r", "bl@ckt0r"))

            soup = BeautifulSoup(r.content.decode(), "html.parser")

            # get max page number
            victim_list = soup.find("table", class_="table").find_all("tr")[1:]

            for victim in victim_list:
                victim_parsed = victim.find_all("td")
                victim_name = victim_parsed[1].text.strip()

                published_dt = datetime.strptime(
                    victim_parsed[0].text.strip(), "%Y/%m")

                victim_leak_site = self.url + "/0x00/" + victim_parsed[5].find("a").attrs["href"]

                q = self.session.query(Victim).filter_by(
                    url=victim_leak_site, site=self.site)

                if q.count() == 0:
                    # new victim
                    r = p.get(victim_leak_site, headers=self.headers,
                            auth=("bl@ckt0r", "bl@ckt0r"))
                    description = r.content.decode()
                    v = Victim(name=victim_name, url=victim_leak_site, published=published_dt,
                               first_seen=datetime.utcnow(), last_seen=datetime.utcnow(), site=self.site, description=description)
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
