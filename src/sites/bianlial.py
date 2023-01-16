from datetime import datetime
import logging

from bs4 import BeautifulSoup

from db.models import Victim
from net.proxy import Proxy
from .sitecrawler import SiteCrawler


class Bianlial(SiteCrawler):
    actor = "Bianlial"

    def __init__(self, url: str):
        super(Bianlial, self).__init__(url)
        self.headers['Host'] = self.url[7:]
        self.headers['Accept'] = 'text/css,*/*;q=0.1'
        self.headers['Accept-Encoding'] = 'gzip, deflate'
        self.headers['Accept-Language'] = 'en-US,en;q=0.5'
        self.headers['Connection'] = 'keep-alive'
        self.headers['Pragma'] = 'no-cache'

    def scrape_victims(self):
        with Proxy() as p:
            r = p.get(f"{self.url}/companies/", headers=self.headers)

            soup = BeautifulSoup(r.content.decode(), "html.parser")

            victim_list = soup.find_all("li", class_="post")

            for victim in victim_list:
                tmp = victim.find("a")
                victim_name = tmp.text.strip()
                if "**" in victim_name:
                    continue
                victim_leak_site = self.url + tmp.attrs["href"]

                q = self.session.query(Victim).filter_by(
                    url=victim_leak_site, site=self.site)

                if q.count() == 0:
                    # new victim
                    published = datetime.strptime(victim.find("span").text.strip(), "%b %d, %Y")
                    r = p.get(victim_leak_site, headers=self.headers)
                    soup = BeautifulSoup(r.content.decode(), "html.parser")
                    description = ""
                    for e in soup.find("section", class_="body").find_all("p"):
                        description += e.get_text() + "\n"

                    v = Victim(name=victim_name, url=victim_leak_site, published=published, first_seen=datetime.utcnow(), last_seen=datetime.utcnow(), site=self.site, description=description)
                    self.session.add(v)
                    self.new_victims.append(v)
                else:
                    # already seen, update last_seen
                    v = q.first()
                    v.last_seen = datetime.utcnow()

                # add the org to our seen list
                self.current_victims.append(v)
            self.session.commit()

        self.site.last_scraped = datetime.utcnow()

        # just for good measure
        self.session.commit()
