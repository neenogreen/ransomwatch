from datetime import datetime
import logging
import re
from bs4 import BeautifulSoup

from db.models import Victim
from net.proxy import Proxy
from .sitecrawler import SiteCrawler

from requests.packages.urllib3.exceptions import InsecureRequestWarning
from requests.packages.urllib3 import disable_warnings

class Karakurt(SiteCrawler):
    actor = "Karakurt"

    def is_site_up(self) -> bool:
        disable_warnings(InsecureRequestWarning)
        with Proxy() as p:
            try:
                r = p.get(self.url, headers=self.headers, verify=False)
                if r.status_code >= 400:
                    return False
            except Exception as e:  
                return False 
        self.site.last_up = datetime.utcnow()
        return True

    def scrape_pre_and_releasing_and_get_pages(self, body: str):
        soup = BeautifulSoup(body, "html.parser")
        victim_list = soup.find_all("article", class_="ciz-post")
        pages = int(soup.find("div", class_="pagination").find_all("a")[-2].get_text().strip())

        for victim in victim_list:
            victim_name = victim.find("h3", class_="post-title").get_text().strip() 
            victim_leak_site = self.url + "/" + victim.find("a").attrs["href"]

            q = self.session.query(Victim).filter_by(
                url=victim_leak_site, site=self.site)

            if q.count() == 0:
                # new victim
                with Proxy() as p:
                    r = p.get(victim_leak_site, headers=self.headers, verify=False)
                soup = BeautifulSoup(r.content.decode(), "html.parser")
                published = datetime.strptime(soup.find("span", class_="post-date").get_text().strip(), "%d %b %Y")
                description = soup.find("article", class_="detail").find("p").get_text().strip()
                v = Victim(name=victim_name, url=victim_leak_site, published=published,
                            first_seen=datetime.utcnow(), last_seen=datetime.utcnow(), site=self.site,
                            description=description)
                self.session.add(v)
                self.new_victims.append(v)
            else:
                # already seen, update last_seen
                v = q.first()
                v.last_seen = datetime.utcnow()

            # add the org to our seen list
            self.current_victims.append(v)
        self.session.commit()

        return pages

    def _handle_page(self, body: str):
        soup = BeautifulSoup(body, "html.parser")
        victim_list = soup.find("div", attrs={"id": "companies_released"}).find_all("li")

        for victim in victim_list:
            victim_name = victim.find("h2", class_="post-title").get_text().strip()
            victim_leak_site = self.url + "/" + victim.find("a").attrs["href"]

            q = self.session.query(Victim).filter_by(
                url=victim_leak_site, site=self.site)

            if q.count() == 0:
                # new victim
                with Proxy() as p:
                    r = p.get(victim_leak_site, headers=self.headers, verify=False)
                soup = BeautifulSoup(r.content.decode(), "html.parser")
                published = datetime.strptime(soup.find("span", class_="post-date").get_text().strip(), "%d %b %Y")
                description = soup.find("article", class_="detail").find("p").get_text().strip()
                v = Victim(name=victim_name, url=victim_leak_site, published=published,
                            first_seen=datetime.utcnow(), last_seen=datetime.utcnow(), site=self.site,
                            description=description)
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
        disable_warnings(InsecureRequestWarning)
        with Proxy() as p:
            r = p.get(f"{self.url}", headers=self.headers, verify=False)
            pages = self.scrape_pre_and_releasing_and_get_pages(r.content.decode()) 

            for i in range(1, pages + 1):
                r = p.get(f"{self.url}/?page={i}&table=releasings", headers=self.headers, verify=False)
                self._handle_page(r.content.decode())

        self.site.last_scraped = datetime.utcnow()
