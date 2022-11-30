from datetime import datetime
import logging
from config import Config
from random import randint
from time import sleep

import json

from db.models import Victim
from net.proxy import Proxy
from .sitecrawler import SiteCrawler


class Alphv(SiteCrawler):
    actor = "Alphv"

    def __init__(self, url: str):
        super(Alphv, self).__init__(url)

        self.headers["Accept"] = "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8"
        self.headers['User-Agent'] = 'Mozilla/5.0 (Windows NT 10.0; rv:91.0) Gecko/20100101 Firefox/91.0'
        self.headers['Accept-Language'] = 'en-US,en;q=0.5'
        self.headers['Accept-Encoding'] = 'gzip, deflate'
        self.headers['Connection'] = 'keep-alive'
        self.headers['Upgrade-Insecure-Requests'] = '1'
        self.headers['Sec-Fetch-Dest'] = 'document'
        self.headers['Sec-Fetch-Mode'] = 'navigate'
        self.headers['Sec-Fetch-Site'] = 'none'
        self.headers['Cache-Control'] = 'max-age=0'
        self.headers['Host'] = self.url[7:]

    def is_site_up(self) -> bool:
        with Proxy() as p:
            try:
                r = p.get(self.url, headers=self.headers, timeout=Config["timeout"])

                if r.status_code >= 400:
                    return False
            except Exception as e:
                return False

        self.site.last_up = datetime.utcnow()

        return True

    def _handle_page(self, body: str):
        victim_list = json.loads(body)
        victim_list = victim_list["items"]

        for victim in victim_list:
            victim_name = victim["title"]
            victim_leak_site = self.url + "/" + victim["id"]
            
            q = self.session.query(Victim).filter_by(
                url=victim_leak_site, site=self.site)

            if q.count() == 0:
                # new victim
                published_dt = datetime.fromtimestamp(int(victim["createdDt"]) / 1000.0)
                v = Victim(name=victim_name, url=victim_leak_site, published=published_dt,
                            first_seen=datetime.utcnow(), last_seen=datetime.utcnow(), site=self.site)
                self.session.add(v)
                self.new_victims.append(v)
            else:
                # already seen, update last_seen
                v = q.first()
                v.last_seen = datetime.utcnow()

            # add the org to our seen list
            self.current_victims.append(v)
        self.session.commit()

    def scrape_victims(self):
        page = 0
        with Proxy() as p:
            while True:
                try:
                    r = p.get(self.url + "/api/blog/all/" + str(page) + "/9", headers=self.headers)
                    if "\"items\":[]" in r.text:
                        break
                    self._handle_page(r.content.decode())
                    page += 9
                except Exception as e:
                    break
        self.site.last_scraped = datetime.utcnow()
