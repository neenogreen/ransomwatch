from datetime import datetime
import logging
import re
from bs4 import BeautifulSoup
import urllib.parse

from db.models import Victim
from net.proxy import Proxy
from .sitecrawler import SiteCrawler

class Nokoyawa(SiteCrawler):
    actor = "Nokoyawa"

    def is_site_up(self) -> bool:
        with Proxy() as p:
            try:
                r = p.get(self.url + "/api/leaks/get")
                if r.status_code >= 400:
                    return False
            except Exception as e:
                return False
        self.site.last_up = datetime.utcnow()
        return True

    def scrape_victims(self):
        with Proxy() as p:
            r = p.get(f"{self.url}/api/leaks/get", headers=self.headers).json()["payload"]

        for victim in r:
            published = datetime.strptime(victim["createdAt"].split(".")[0], "%Y-%m-%dT%H:%M:%S")
            description = victim["description"]
            victim_url = self.url + "/leak/" + victim["_id"]
            victim_name = urllib.parse.unquote(victim["title"])
            
            q = self.session.query(Victim).filter_by(
                name=victim_name, url=victim_url, site=self.site)

            if q.count() == 0:
                # new victim
                v = Victim(name=victim_name, published=published, description=description, first_seen=datetime.utcnow(), last_seen=datetime.utcnow(), site=self.site, url=victim_url)
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
