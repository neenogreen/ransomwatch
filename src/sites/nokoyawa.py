from datetime import datetime
import logging
import re
from bs4 import BeautifulSoup

from db.models import Victim
from net.proxy import Proxy
from .sitecrawler import SiteCrawler

class Nokoyawa(SiteCrawler):
    actor = "Nokoyawa"

    def scrape_victims(self):
        with Proxy() as p:
            r = p.get(f"{self.url}", headers=self.headers)
        soup = BeautifulSoup(r.content.decode(), "html.parser")
        victim_list = soup.find_all("div", {'id': re.compile(r'overlay')})

        for victim in victim_list:
            tmp = victim.find("h3")
            published_str = tmp.find("span").text.strip()
            try:
                published = datetime.strptime(published_str, "(%b. %d, %Y, ")
            except ValueError as v:
                if len(v.args) > 0 and v.args[0].startswith('unconverted data remains: '):
                    line = published_str[:-(len(v.args[0]) - 26)]
                    published = datetime.strptime(line, "(%b. %d, %Y, ")
                else:
                    raise
            victim_name = tmp.text.strip().replace(published_str, "").replace("\n", "").strip()
            
            q = self.session.query(Victim).filter_by(
                name=victim_name, site=self.site)

            if q.count() == 0:
                # new victim
                description = victim.find("p").text.strip()
                v = Victim(name=victim_name, published=published, description=description, first_seen=datetime.utcnow(), last_seen=datetime.utcnow(), site=self.site)
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
