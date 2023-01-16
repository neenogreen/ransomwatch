from datetime import datetime
import logging
from config import Config

import json
from bs4 import BeautifulSoup

from db.models import Victim
from net.proxy import Proxy
from .sitecrawler import SiteCrawler


class Play(SiteCrawler):
    actor = "Play"

    def _handle_page(self, body: str):
        soup = BeautifulSoup(body, "html.parser")
        victim_list = soup.find_all("th", class_="News")

        for victim in victim_list:
            if not victim.find("h", attrs={"style": "color: #F5F5F5;"}):
                continue
            victim_name = victim.text.strip().split(",")[0]
            victim_leak_site = self.url + "/topic.php?id=" + victim.attrs["onclick"].split("'")[1]

            q = self.session.query(Victim).filter_by(
                url=victim_leak_site, site=self.site)

            if q.count() == 0:
                # new victim
                published_dt = datetime.strptime(victim.get_text().strip().split("publication date: ")[1][:10], "%Y-%m-%d")
                with Proxy() as p:
                    r = p.get(victim_leak_site, headers=self.headers)
                    tmp = BeautifulSoup(r.content.decode(), "html.parser").find("div", attrs={"style": "font-weight: 100;line-height: 1.75;"}).find_all()
                    victim_description = ""
                    for e in tmp:
                        tmp2 = e.find_all(text=True, recursive=False)
                        for f in tmp2:
                            victim_description += f.strip() + "\n"

                v = Victim(name=victim_name, description=victim_description, url=victim_leak_site, published=published_dt, first_seen=datetime.utcnow(), last_seen=datetime.utcnow(), site=self.site)
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
        with Proxy() as p:
            main = p.get(f"{self.url}", headers=self.headers)
            size = len(BeautifulSoup(main.content.decode(), "html.parser").find_all("span", class_="Page"))
            for page in range(1, size + 1):
                r = p.get(f"{self.url}/index.php?page={str(page)}", headers=self.headers)
                self._handle_page(r.content.decode())

        self.site.last_scraped = datetime.utcnow()
