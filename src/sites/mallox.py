from datetime import datetime
import logging

from bs4 import BeautifulSoup

from db.models import Victim
from net.proxy import Proxy
from .sitecrawler import SiteCrawler

import string
import random

class Mallox(SiteCrawler):
    actor = "Mallox"

    def scrape_victims(self):
        with Proxy() as p:
            r = p.get(f"{self.url}/post?get_listBlog", headers=self.headers)

            soup = BeautifulSoup(r.content.decode(), "html.parser")

            victim_list = soup.find_all("div", class_="card-body")

            for victim in victim_list:
                victim_name = victim.find("h4", class_="card-title").text.strip()
                try:
                    victim_leak_site = self.url + victim.find("a").attrs["href"]
                except:
                    victim_leak_site = None

                if not victim_leak_site:
                    q = self.session.query(Victim).filter_by(
                        name=victim_name, site=self.site)
                    victim_leak_site = ''.join(random.choices(string.ascii_lowercase +
                                                     string.digits, k=16))
                else:
                    q = self.session.query(Victim).filter_by(
                        url=victim_leak_site, site=self.site)


                if q.count() == 0:
                    # new victim
                    published = datetime.strptime(victim.find("span", class_="badge badge-info").text.strip(), "%d/%m/%Y %H:%M")
                    description = ""
                    for e in victim.find_all("p"):
                        description += e.text.strip() + "\n"
                    description = description[:-1]

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
