from datetime import datetime
import logging

from bs4 import BeautifulSoup

from db.models import Victim
from net.proxy import Proxy
from .sitecrawler import SiteCrawler


class Everest(SiteCrawler):
    actor = "Everest"

    def extract_description(self, body: str):
        soup = BeautifulSoup(body, "html.parser")
        desc_html = soup.find("div", class_="entry-content")
        p_lines = desc_html.find_all("p")
        description = ""

        for line in p_lines:
            description += line.text.strip()
            description += "\n"

        return description

    def _handle_page(self, body: str, p: Proxy):
        soup = BeautifulSoup(body, "html.parser")

        victim_list = soup.find_all(
            "header", class_="entry-header has-text-align-center")

        for victim in victim_list:
            victim_name = victim.find(
                "h2", class_="entry-title heading-size-1").text.strip()

            victim_leak_site = victim.find(
                "h2", class_="entry-title heading-size-1").find("a").attrs["href"]

            published_dt = datetime.now()

            q = self.session.query(Victim).filter_by(
                url=victim_leak_site, site=self.site)

            if q.count() == 0:
                # new victim
                r = p.get(victim_leak_site, headers=self.headers)
                description = self.extract_description(r.content.decode())
                v = Victim(name=victim_name, description=description, url=victim_leak_site, published=published_dt, first_seen=datetime.utcnow(), last_seen=datetime.utcnow(), site=self.site)
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
            r = p.get(f"{self.url}", headers=self.headers)
            soup = BeautifulSoup(r.content.decode(), "html.parser")

            # find all pages
            page_nav = soup.find_all("a", class_="page-numbers")

            site_list = []
            site_list.append(self.url)

            for page in page_nav:
                # might exist repetition
                if page.attrs["href"] not in site_list:
                    site_list.append(page.attrs["href"])
            max_page = 0
            min_page = 1000

            for site in site_list:
                site_splitted = site.split("/")
                #print("Site_splitted: ")
                # print(site_splitted)
                if (len(site_splitted) >= 4 and site_splitted[4].isdigit() and max_page < int(site_splitted[4])):
                    max_page = int(site_splitted[4])
                if (len(site_splitted) >= 4 and site_splitted[4].isdigit() and min_page > int(site_splitted[4])):
                    min_page = int(site_splitted[4])
            #print("Max Page: "+str(max_page))
            #print("Min Page: "+str(min_page))

            base_site = site_list[0]
            r = p.get(base_site, headers=self.headers)
            self._handle_page(r.content.decode(), p)

            for pagenum in range(min_page, max_page+1):
                site_tovisit = base_site + \
                    "/page/"+str(pagenum)+"/"
                #print("Site "+site_tovisit)
                r = p.get(site_tovisit, headers=self.headers)
                self._handle_page(r.content.decode(), p)

            self.site.last_scraped = datetime.utcnow()
            self.session.commit()
            # for site in site_list:
            #    if (site.startswith("//")):
            #        site = "https:"+site
            #    print("Site "+site)
            #    r = p.get(site, headers=self.headers)
            #    self._handle_page(r.content.decode())
