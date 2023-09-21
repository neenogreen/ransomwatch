from datetime import datetime
import logging

from bs4 import BeautifulSoup

from net.proxy import Proxy
from .sitecrawler import SiteCrawler
from net.headless_browser import HeadlessBrowser
from time import sleep
from captcha_solver import CaptchaSolver
from config import Config
from notifications.manager import NotificationManager

class Cloak(SiteCrawler):
    actor = "Cloak"

    def is_site_up(self) -> bool: 
        self.headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; rv:102.0) Gecko/20100101 Firefox/102.0"}   
        with Proxy() as p:
            try:   
                r = p.get(self.url+"/verify_captcha", headers=self.headers) 
                if "CAPTCHA Verification" not in r.text:   
                    return False  
            except Exception as e:
                return False 
            self.site.last_up = datetime.utcnow()   
            return True

    def _handle_page(self, browser):
        print(browser.res())
        soup = BeautifulSoup(browser.res(), "html.parser")

        victim_list = soup.find_all("div", class_="main__items ")
        for victim in victim_list:
            victim_name = victim.find("h2").text.strip()
            victim_leak_site = self.url + f"/{victim_name.lower()}"
            description = victim.find("div", class_="main__info").get_text()
            q = self.session.query(Victim).filter_by(
                url=victim_leak_site, site=self.site_id, name=victim_name)

            if q.count() == 0:
                # new victim
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
                with Proxy() as p:
                    r = p.get(self.url+"/verify_captcha", headers=self.headers) 
                    self.cookies = p.session.cookies.get_dict()
                browser.get(self.url)
                browser.DRIVER.add_cookie({"name": "session", "value": self.cookies["session"]})
                browser.get(self.url+"/verify_captcha")
                browser.find_element_by_css_selector("body > form:nth-child(2) > button:nth-child(5)").click()
                sleep(10)
                browser.find_element_by_css_selector("body > form:nth-child(2) > img:nth-child(3)").screenshot("/app/captcha-cloak.png")
                with open("/app/captcha-cloak.png", "rb") as img:
                    captcha = img.read()
                try:
                    captcha = CaptchaSolver('2captcha', api_key=Config["2captcha_key"]).solve_captcha(captcha)
                    print(captcha)
                    browser.find_element_by_name("captcha_input").send_keys(captcha)
                    browser.find_element_by_css_selector("body > form:nth-child(2) > button:nth-child(5)").click()
                except:
                    continue
                sleep(10)
                print(browser.res())
                try:
                    browser.find_element_by_name("captcha_input")
                except:
                    self._handle_page(browser)
                    break
            if i == 4: NotificationManager.send_error_notification("Cloak error", "Cloak failed in solving captcha 5 times in a row")
