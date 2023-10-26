from datetime import datetime
from time import mktime
import logging
import feedparser

from bs4 import BeautifulSoup

from db.models import Victim
from net.proxy import Proxy
from .sitecrawler import SiteCrawler


class DataLeak(SiteCrawler):
    actor = "DataLeak"

    def scrape_victims(self):
        with Proxy() as p:
            r = p.get(f"{self.url}/atom.xml", headers=self.headers)

            victim_list = feedparser.parse(r.content.decode()).entries

            for victim in victim_list:
                victim_name = victim.title
                victim_leak_site = victim.id

                q = self.session.query(Victim).filter_by(
                    url=victim_leak_site, site=self.site)

                if q.count() == 0:
                    # new victim
                    published = datetime.fromtimestamp(mktime(victim.updated_parsed))
                    description = BeautifulSoup(victim.summary, "lxml").get_text()

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
