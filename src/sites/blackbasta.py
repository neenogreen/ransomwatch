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

class Blackbasta(SiteCrawler):
    actor = "Blackbasta"

    def __init__(self, url: str):
        super(Blackbasta, self).__init__(url)

    def is_site_up(self) -> bool:
        with Proxy() as p:
            try:
                r = p.get(self.url, headers=self.headers)

                if r.status_code >= 400:
                    return False
            except Exception as e:
                print(e)
                return False

        self.site.last_up = datetime.utcnow()

        return True

    def _handle_page(self, browser):
        while True:
            soup = BeautifulSoup(browser.res(), "html.parser")

            victim_list = soup.find_all("div", class_=['card'])

            for victim in victim_list:
                tmp = victim.find("a", class_="blog_name_link")
                victim_name = tmp.text.strip()
                victim_leak_site = tmp["href"]
                
                q = self.session.query(Victim).filter_by(
                    url=victim_leak_site, site=self.site)

                if q.count() == 0:
                    # new victim
                    description = victim.find("div", class_="vuepress-markdown-body").get_text().strip()
                    v = Victim(name=victim_name, description=description, url=victim_leak_site, published=datetime.utcnow(), first_seen=datetime.utcnow(), last_seen=datetime.utcnow(), site=self.site)
                    self.session.add(v)
                    self.new_victims.append(v)
                else:
                    # already seen, update last_seen
                    v = q.first()
                    v.last_seen = datetime.utcnow()

                # add the org to our seen list
                self.current_victims.append(v)
            try:
                browser.DRIVER.find_element(By.XPATH, '//div[@class="next-page-btn"]').click()
            except NoSuchElementException:
                break

            sleep(10)

        self.session.commit()

    def scrape_victims(self):
        with HeadlessBrowser() as browser:
            browser.get(f"{self.url}")
            sleep(15)
            self._handle_page(browser)
        self.site.last_scraped = datetime.utcnow()

