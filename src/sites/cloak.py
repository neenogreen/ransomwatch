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
from db.models import Victim

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

    def _handle_page(self, page):
        soup = BeautifulSoup(page, "html.parser")

        victim_list = soup.select('div[class*="main__items"]')
        for victim in victim_list:
            victim_name = victim.find("h2").text.strip()
            victim_leak_site = self.url + f"/{victim_name}"
            description = victim.find("div", class_="main__info").get_text()
            q = self.session.query(Victim).filter_by(
                url=victim_leak_site, site=self.site, name=victim_name)

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
        with Proxy() as p:
            for i in range(10):
                r = p.get(self.url+"/verify_captcha", headers=self.headers)
                soup = BeautifulSoup(r.text, "lxml")
                csrf_token = soup.find("input")["value"]
                headers_local = self.headers.copy()
                headers_local["Cookie"] = f"session={p.session.cookies.get_dict()['session']}"
                headers_local["Referer"] = f"{self.url}/verify_captcha"
                headers_local["Origin"] = self.url
                r = p.get(self.url + soup.find("img")["src"], headers=headers_local)
                captcha = r.content
                headers_local["Cookie"] = f"session={p.session.cookies.get_dict()['session']}"
                captcha = CaptchaSolver('2captcha', api_key=Config["2captcha_key"]).solve_captcha(captcha)
                r = p.post(self.url+"/verify_captcha", headers=headers_local, data={"csrf_token": csrf_token, "captcha_input": captcha}, allow_redirects=False)
                if r.status_code == 302:
                    headers_local["Cookie"] = f"session={p.session.cookies.get_dict()['session']}"
                    r = p.get(self.url, headers=headers_local)
                    self._handle_page(r.text)
                    break
            if i == 4: NotificationManager.send_error_notification("Cloak error", "Cloak failed in solving captcha 5 times in a row")
