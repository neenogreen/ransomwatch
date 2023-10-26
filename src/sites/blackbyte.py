from datetime import datetime
import logging

from bs4 import BeautifulSoup
from time import sleep

from db.models import Victim
from net.proxy import Proxy
from net.headless_browser import HeadlessBrowser
from .sitecrawler import SiteCrawler


class Blackbyte(SiteCrawler):
    actor = "Blackbyte"

    def _handle_page(self, browser):
        soup = BeautifulSoup(browser.res(), "html.parser")

        victim_list = soup.select('div[class*="col-sm-12"]')

        for victim in victim_list:
            if "If you are interested to purchase the data" in str(victim): continue
            victim_name = victim.find("h1").text.strip()
            description = victim.find("p").text.strip()

            published_dt = datetime.now()
            
            q = self.session.query(Victim).filter_by(
                name=victim_name, site=self.site)

            if q.count() == 0:
                # new victim
                v = Victim(name=victim_name, description=description, url=None, published=published_dt,
                            first_seen=datetime.utcnow(), last_seen=datetime.utcnow(), site=self.site)
                self.session.add(v)
                self.new_victims.append(v)
            else:
                # already seen, update last_seen
                v = q.first()
                v.last_seen = datetime.utcnow()

            # add the org to our seen list
            self.current_victims.append(v)
        self.site.last_scraped = datetime.utcnow()
        self.session.commit()


    def scrape_victims(self):
        with HeadlessBrowser() as browser:
            browser.get(f"{self.url}")
            sleep(15) 
            self._handle_page(browser)
