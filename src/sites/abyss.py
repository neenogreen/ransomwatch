from datetime import datetime
import logging
import re
from bs4 import BeautifulSoup
import urllib.parse

from db.models import Victim
from net.proxy import Proxy
from .sitecrawler import SiteCrawler

class Abyss(SiteCrawler):
    actor = "Abyss"

    def is_site_up(self) -> bool:
        with Proxy() as p:
            try:
                r = p.get(self.url + "/static/data.js")
                if r.status_code >= 400:
                    return False
            except Exception as e:
                return False
        self.site.last_up = datetime.utcnow()
        return True

    def scrape_victims(self):
        with Proxy() as p:
            r = p.get(f"{self.url}/static/data.js", headers=self.headers)

        victims = []
        for line in r.text.split("\n"):
            if "'title' : '" in line:
                victims.append({"title": line.split("'")[3], "description": ""})
            if "'short' : '" in line:
                victims[-1]["description"] = line.split("'")[3]

        for victim in victims:
            q = self.session.query(Victim).filter_by(
                name=victim["title"], site=self.site)

            if q.count() == 0:
                # new victim
                v = Victim(name=victim["title"], published=datetime.utcnow(), description=victim["description"], first_seen=datetime.utcnow(), last_seen=datetime.utcnow(), site=self.site)
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
