from datetime import datetime
import logging
from config import Config
from random import randint
from time import sleep

from bs4 import BeautifulSoup

from db.models import Victim
from net.proxy import Proxy
from net.headless_browser import HeadlessBrowser
from .sitecrawler import SiteCrawler
from notifications.manager import NotificationManager

class Lockbit(SiteCrawler):
    actor = "Lockbit"

    def __init__(self, url: str):
        super(Lockbit, self).__init__(url)

    def is_site_up(self) -> bool:
        with Proxy() as p:
            try:
                r = p.get(self.url, headers=self.headers)

                if r.status_code >= 400:
                    return False
            except Exception as e:
                #print(e)
                return False

        self.site.last_up = datetime.utcnow()

        return True

    def _handle_page(self, browser):
        soup = BeautifulSoup(browser.res(), "html.parser")

        victim_list = soup.find_all("div", class_=['post-block bad', 'post-block good'])

        for victim in victim_list:
            victim_name = victim.find("div", class_="post-title").text.strip()
            victim_leak_site = self.url + victim["onclick"].split("'")[1]
            
            q = self.session.query(Victim).filter_by(
                url=victim_leak_site, site=self.site)

            if q.count() == 0:
                # new victim
                browser.get(f"{victim_leak_site}")
                soup1 = BeautifulSoup(browser.res(), "html.parser")
                deadline = soup1.find_all("p", class_="post-banner-p")[0].text.strip()[10:]
                description = soup1.find("div", class_="desc").text.strip()

                published_dt = datetime.strptime(deadline, "%d %b, %Y %H:%M:%S %Z")
                v = Victim(name=victim_name, description=description, url=victim_leak_site, published=published_dt, first_seen=datetime.utcnow(), last_seen=datetime.utcnow(), site=self.site)
                self.session.add(v)
                self.new_victims.append(v)
            else:
                # already seen, update last_seen
                v = q.first()
                if victim.find("div", class_="post-timer-end"):
                    if v.first_seen < v.published and v.published <= datetime.utcnow():
                        NotificationManager.send_new_victim_notification(v)
                        v.first_seen = v.published
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
