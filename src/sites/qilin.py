from datetime import datetime
import logging

from bs4 import BeautifulSoup

from db.models import Victim
from net.proxy import Proxy
from .sitecrawler import SiteCrawler


class Qilin(SiteCrawler):
    actor = "Qilin"

    def scrape_victims(self):
        with Proxy() as p:
            r = p.get(f"{self.url}", headers=self.headers)

            soup = BeautifulSoup(r.content.decode(), "html.parser")

            victim_list = soup.select("[data-key]")

            for victim in victim_list:
                tmp = victim.find("a", class_="item_box-title mb-2 mt-1")
                victim_name = tmp.text.strip()
                victim_leak_site = self.url + tmp.attrs["href"]

                q = self.session.query(Victim).filter_by(
                    url=victim_leak_site, site=self.site)

                if q.count() == 0:
                    # new victim
                    published = datetime.strptime(victim.find_all("div", class_="item_box-info__item d-flex align-items-center")[1].get_text().strip(), "%b %d, %Y")
                    r = p.get(victim_leak_site, headers=self.headers)
                    soup = BeautifulSoup(r.content.decode(), "html.parser")
                    description = soup.find("div", class_="col-md-8 col-xl-6").text.strip()

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
