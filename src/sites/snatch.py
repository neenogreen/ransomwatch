from datetime import datetime
import logging
import re
from bs4 import BeautifulSoup

from db.models import Victim
from net.proxy import Proxy
from .sitecrawler import SiteCrawler

class Snatch(SiteCrawler):
    actor = "Snatch"

    def _handle_page(self, body: str):
        soup = BeautifulSoup(body, "html.parser")
        victim_list = soup.find_all("div", class_="ann-block")

        for victim in victim_list:
            victim_name = victim.find("div", class_="a-b-name").text.strip().split("Data Added: ")[0]
            victim_leak_site = self.url + "/" + victim.find("button", class_="a-b-b-r-l-button").attrs["onclick"].split("'")[1]

            q = self.session.query(Victim).filter_by(
                url=victim_leak_site, site=self.site)

            if q.count() == 0:
                # new victim
                with Proxy() as p:
                    r = p.get(victim_leak_site, headers=self.headers)
                soup = BeautifulSoup(r.content.decode(), "html.parser")
                published_str = soup.find("div", class_="n-n-c-e-t-time").get_text().split("\n")[1].strip()
                published_dt = datetime.strptime(published_str, "Created: %b %d, %Y %I:%M %p")
                description = soup.find("div", class_="n-n-c-e-text").get_text().strip()
                v = Victim(name=victim_name, url=victim_leak_site, published=published_dt, description=description, first_seen=datetime.utcnow(), last_seen=datetime.utcnow(), site=self.site)
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
        # New
        page = 1
        with Proxy() as p:
            r = p.get(f"{self.url}/index.php?page={page}&filter=new", headers=self.headers)
            page_new_max = len(BeautifulSoup(r.content.decode(), "html.parser").find("div", class_="main-nav-numbers").find_all("a"))
            while page <= page_new_max:
                r = p.get(f"{self.url}/index.php?page={page}&filter=new", headers=self.headers)
                self._handle_page(r.content.decode()) 
                page += 1
        # Full
        page = 1
        with Proxy() as p:
            r = p.get(f"{self.url}/index.php?page={page}&filter=full", headers=self.headers)
            page_new_max = len(BeautifulSoup(r.content.decode(), "html.parser").find("div", class_="main-nav-numbers").find_all("a"))
            while page <= page_new_max:
                r = p.get(f"{self.url}/index.php?page={page}&filter=full", headers=self.headers)
                self._handle_page(r.content.decode()) 
                page += 1
        self.site.last_scraped = datetime.utcnow()
