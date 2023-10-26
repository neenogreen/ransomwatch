from datetime import datetime
import logging

from bs4 import BeautifulSoup

from db.models import Victim
from net.proxy import Proxy
from .sitecrawler import SiteCrawler


class Cuba(SiteCrawler):
    actor = "Cuba"

    def extract_published_date_and_description(self, body: str):
        soup = BeautifulSoup(body, "html.parser")

        p_lines = soup.find_all("p")

        published = None
        description = ""

        for line in p_lines:
            line_description = line.text.strip()
            # They hard-code everything
            if "Date" in line_description:
                published = line_description[len(
                    "Date the files were received: "):]
            elif "website:" in line_description:
                continue
            else:
                description += line_description
                description += "\n"

        if "." in published:
            published = published.replace(".", "")
        if published[0] == " ":
            published = published[1:]
        date_split = published.split(" ")
        if len(date_split) == 2:
            day = date_split[0]
            month = date_split[1][:-4]
            year = date_split[1][-4:]
        elif len(date_split) == 3:
            day = date_split[0]
            month = date_split[1]
            year = date_split[2]
        else:
            day = "01"
            month = "January"
            year = "1970"

        if "-" in day:
            day = day.split("-")[0]

        if month == "01":
            month = "January"

        if month == "febriary":
            month = "February"

        if month == "Jule":
            month = "July"

        published = day + " " + month + " " + year

        return datetime.strptime(published, "%d %B %Y"), description

    def _handle_page(self, body: str, p: Proxy):
        soup = BeautifulSoup(body, "html.parser")

        victim_list = soup.find_all("div", class_="list-text")

        for victim in victim_list:
            # extract victim name from url
            victim_name = victim.find("a").attrs["href"][9:]
            # they put the published date in the victim's leak page
            victim_leak_site = self.url + victim.find("a").attrs["href"]

            q = self.session.query(Victim).filter_by(
                url=victim_leak_site, site=self.site)

            if q.count() == 0:
                # new victim
                r = p.get(victim_leak_site, headers=self.headers)
                published_dt, description = self.extract_published_date_and_description(r.content.decode())
                v = Victim(name=victim_name, description=description, url=victim_leak_site, published=published_dt, first_seen=datetime.utcnow(), last_seen=datetime.utcnow(), site=self.site)
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
        with Proxy() as p:
            cnt = 0
            while True:
                r = p.get(f"{self.url}/ajax/page_free/{cnt}", headers=self.headers)
                if "nomore" in r.content.decode():
                    break

                soup = BeautifulSoup(r.content.decode(), "html.parser")
                self._handle_page(r.content.decode(), p)
                cnt += 1
