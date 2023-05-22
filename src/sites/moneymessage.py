from datetime import datetime
import logging
from config import Config
from random import randint
from time import sleep

from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException

from db.models import Victim
from net.proxy import Proxy
from net.headless_browser import HeadlessBrowser
from .sitecrawler import SiteCrawler
from notifications.manager import NotificationManager

class MoneyMessage(SiteCrawler):
    actor = "MoneyMessage"

    def __init__(self, url: str):
        super(MoneyMessage, self).__init__(url)

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
        if "Wrong page of news..." in browser.res():
            return False

        soup = BeautifulSoup(browser.res(), "html.parser")

        victim = soup.find("div", class_=['MuiBox-root css-0'])

        name = victim.find("h5").text
        try:
            try:
                published = datetime.strptime(victim.find("p").text, "%m.%d.%Y")
            except:
                published = datetime.strptime(victim.find("p").text, "%d.%m.%Y")
        except:
            try:
                published = datetime.strptime(victim.find("p").text, "%m-%d-%Y")
            except:
                published = datetime.strptime(victim.find("p").text, "%d-%m-%Y")
        description = ""
        for e in victim.findAll("p", text=True):
            description += e.text + "\n"
        leak_site = victim.find_all("a")[-1]["href"]
        
        q = self.session.query(Victim).filter_by(
            url=leak_site, site=self.site)

        if q.count() == 0:
            # new victim
            v = Victim(name=name, description=description, url=leak_site, published=published, first_seen=datetime.utcnow(), last_seen=datetime.utcnow(), site=self.site)
            self.session.add(v)
            self.new_victims.append(v)
        else:
            # already seen, update last_seen
            v = q.first()
            v.last_seen = datetime.utcnow()

        # add the org to our seen list
        self.current_victims.append(v)
        return True

    def scrape_victims(self):
        with HeadlessBrowser() as browser:
            i = 1
            while True:
                browser.get(f"{self.url}/news.php?id={i}")
                sleep(10)
                if not self._handle_page(browser):
                    break
                i = i + 1
        self.site.last_scraped = datetime.utcnow()
        self.session.commit()
