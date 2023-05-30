from datetime import datetime
import logging

from bs4 import BeautifulSoup

from db.models import Victim
from net.proxy import Proxy
from .sitecrawler import SiteCrawler
from net.headless_browser import HeadlessBrowser
from time import sleep
from captcha_solver import CaptchaSolver
from config import Config
import base64
from notifications.manager import NotificationManager

class Cl0p(SiteCrawler):
    actor = "Cl0p"

    def _handle_page(self, browser):
        soup = BeautifulSoup(browser.res(), "html.parser")

        # get max page number
        victim_list = soup.find("ul", class_="g-toplevel").find_all("li", class_="g-menu-item")
        victim_list.extend(soup.find("ul", class_="g-toplevel").find("li", class_="g-menu-item-archive").find("ul", class_="g-sublevel").find_all("li")[1:])
        victim_list.extend(soup.find("ul", class_="g-toplevel").find("li", class_="g-menu-item-archive2").find("ul", class_="g-sublevel").find_all("li")[1:])
        victim_list.extend(soup.find("ul", class_="g-toplevel").find("li", class_="g-menu-item-archive3").find("ul", class_="g-sublevel").find_all("li")[1:])
        for victim in victim_list:
            victim_name = victim.find("span", class_="g-menu-item-title").text.strip()
            if victim_name in ("HOME", "HOW TO DOWNLOAD?", "ARCHIVE", "ARCHIVE2", "ARCHIVE3"):
                continue
            victim_leak_site = self.url + victim.find("a").attrs["href"]
            q = self.session.query(Victim).filter_by(
                name=victim_name, site=self.site)

            if q.count() == 0:
                # new victim
                r = browser.get(victim_leak_site)
                soup1 = BeautifulSoup(browser.res(), "html.parser")

                description = soup1.find("p").text.strip()
                if "Due to the fact that the Tor network is abandoning the second version and all domains will be abolished in September or October, we are moving to a new address" in description:
                    description = soup1.find_all("p")[1].text.strip()
                
                v = Victim(name=victim_name, url=victim_leak_site,
                        description=description,
                        published=datetime.utcnow(),
                        first_seen=datetime.utcnow(),
                        last_seen=datetime.utcnow(), site=self.site)
                self.session.add(v)
                self.new_victims.append(v)
            else:
                # already seen, update last_seen
                v = q.first()
                v.last_seen = datetime.utcnow()

            # add the org to our seen list
            self.current_victims.append(v)
        self.site.last_scraped = datetime.utcnow()
        # just for good measure
        self.session.commit()

    def scrape_victims(self):
        with HeadlessBrowser() as browser:
            for i in range(5):
                browser.get(self.url)
                sleep(20)
                soup = BeautifulSoup(browser.res(), "html.parser")
                try:
                    captcha = base64.b64decode(soup.find("div", class_="captchav2").find("div")["style"].split("base64,")[1][:-2])
                    captcha = CaptchaSolver('2captcha', api_key=Config["2captcha_key"]).solve_captcha(captcha)
                    browser.find_element_by_name("cap").send_keys(captcha)
                    browser.find_element_by_class("before").click()
                except:
                    continue
                sleep(20)
                browser.res()
                try:
                    browser.find_element_by_name("cap")
                except:
                    self._handle_page(browser)
                    break
            if i == 5: NotificationManager.send_error_notification("Cl0p error", "Cl0p failed in solving captcha 5 times in a row")
