from datetime import datetime
import logging
from config import Config
from random import randint
from time import sleep

from bs4 import BeautifulSoup

from db.models import Victim
from net.proxy import Proxy
from .sitecrawler import SiteCrawler
from notifications.manager import NotificationManager


class Lockbit(SiteCrawler):
    actor = "Lockbit"

    def __init__(self, url: str):
        super(Lockbit, self).__init__(url)

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
                r = p.get(self.url, headers=self.headers)

                if r.status_code >= 400:
                    return False
            except Exception as e:
                print(e)
                return False

        self.site.last_up = datetime.utcnow()

        return True

    def _handle_page(self, body: str):
        soup = BeautifulSoup(body, "html.parser")

        victim_list = soup.find_all("div", class_=['post-block bad', 'post-block good'])

        for victim in victim_list:
            victim_name = victim.find("div", class_="post-title").text.strip()
            victim_leak_site = self.url + victim["onclick"].split("'")[1]
            
            q = self.session.query(Victim).filter_by(
                url=victim_leak_site, site=self.site)

            if q.count() == 0:
                # new victim
                while True:
                    try:
                        with Proxy() as p:
                            r = p.get(f"{victim_leak_site}", headers=self.headers)
                        break
                    except:
                        sleep(randint(1,2))
                        pass
                soup1 = BeautifulSoup(r.content.decode(), "html.parser")
                deadline = soup1.find_all("p", class_="post-banner-p")[0].text.strip()[10:]

                published_dt = datetime.strptime(deadline, "%d %b, %Y %H:%M:%S %Z")
                v = Victim(name=victim_name, url=victim_leak_site, published=published_dt,
                            first_seen=datetime.utcnow(), last_seen=datetime.utcnow(), site=self.site)
                self.session.add(v)
                self.new_victims.append(v)
                sleep(randint(1,2))
            else:
                # already seen, update last_seen
                v = q.first()
                if victim.find("div", class_="post-timer-end d-none"):
                    if v.first_seen < v.published and v.published <= datetime.utcnow():
                        NotificationManager.send_new_victim_notification(v)
                        v.first_seen = v.published
                v.last_seen = datetime.utcnow()

            # add the org to our seen list
            self.current_victims.append(v)
        self.site.last_scraped = datetime.utcnow()
        self.session.commit()

    def scrape_victims(self):
        with Proxy() as p:
            r = p.get(f"{self.url}", headers=self.headers)
            self._handle_page(r.content.decode()) 
