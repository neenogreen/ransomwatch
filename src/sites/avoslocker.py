from datetime import datetime
from bs4 import BeautifulSoup
import logging

from config import Config
from db.models import Victim
from net.proxy import Proxy
from net.headless_browser import HeadlessBrowser
from .sitecrawler import SiteCrawler
import base64
from time import sleep
from captcha_solver import CaptchaSolver
from notifications.manager import NotificationManager

class Avoslocker(SiteCrawler):
    actor = "Avoslocker"

    def _handle_page(self, browser):
        soup = BeautifulSoup(browser.res(), "html.parser")
        victims = soup.find_all("div", class_="card")
        victims += soup.find_all("div", calss_="card leak")

        for item in victims:
            name = item.find("h5", class_="card-brand").text.strip()
            publish_dt = datetime.strptime(item.find("div", class_="card-footer").find("span").text.strip().split(" ")[1], "%m/%d/%Y")
            leak_site = self.url + item.find("div", class_="card-footer").find("div", class_="buttons").find("a")["href"]
            description = item.find("div", class_="card-desc").text.strip()

            q = self.session.query(Victim).filter_by(site=self.site, name=name, url=leak_site)

            if q.count() == 0:
                # new victim
                v = Victim(name=name, url=leak_site, published=publish_dt, first_seen=datetime.utcnow(), last_seen=datetime.utcnow(), site=self.site, description=description)
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
            for i in range(5):
                browser.get(self.url)
                while "Prove that you are human" not in browser.res():
                    sleep(1)
                try:
                    soup = BeautifulSoup(browser.res(), "html.parser")
                    captcha = base64.b64decode(soup.find("div", class_="captchav2").find("div")["style"].split("base64,")[1][:-2])
                    captcha = CaptchaSolver('2captcha', api_key=Config["2captcha_key"]).solve_captcha(captcha)
                    if ":" in captcha:
                        captcha = captcha.split(":")
                    else:
                        captcha = captcha.split(".")
                    h = captcha[0].rjust(2, "0")
                    m = captcha[1].rjust(2, "0")
                    sel = browser.find_elements_by_name("cap")
                    sel_h = browser.select(sel[0])
                    sel_h.select_by_value(h)
                    sel_m = browser.select(sel[1])
                    sel_m.select_by_value(m)
                    browser.find_element_by_class("before").click()
                except:
                    browser.DRIVER.delete_all_cookies();
                    browser.new_identity()
                    continue
                sleep(10)
                browser.res()
                try:
                    browser.find_element_by_name("cap")
                except:
                    self._handle_page(browser)
                    break
            if i == 4: NotificationManager.send_error_notification("AvosLocker error", "AvosLocker failed in solving captcha 5 times in a row")
