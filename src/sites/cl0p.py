from datetime import datetime
import logging

from bs4 import BeautifulSoup

from db.models import Victim
from net.proxy import Proxy
from .sitecrawler import SiteCrawler


class Cl0p(SiteCrawler):
    actor = "Cl0p"

    def scrape_victims(self):
        with Proxy() as p:
            r = p.get(f"{self.url}", headers=self.headers)

            soup = BeautifulSoup(r.content.decode(), "html.parser")

            # get max page number
            victim_list = soup.find("ul", class_="g-toplevel").find_all("li", class_="g-menu-item")
            victim_list.extend(soup.find("ul", class_="g-toplevel").find("li", class_="g-menu-item-archive").find("ul", class_="g-sublevel").find_all("li")[1:])
            victim_list.extend(soup.find("ul", class_="g-toplevel").find("li", class_="g-menu-item-archive2").find("ul", class_="g-sublevel").find_all("li")[1:])
            victim_list.extend(soup.find("ul", class_="g-toplevel").find("li", class_="g-menu-item-archive3").find("ul", class_="g-sublevel").find_all("li")[1:])
            for victim in victim_list:
                victim_name = victim.find("span", class_="g-menu-item-title").text.strip()
                if victim_name in ("HOME", "HOW TO DOWNLOAD?", "ARCHIVE", "ARCHIVE2", "ARCHIVE3"):
                    continue
                victim_leak_site = self.url + victim.find("a").attrs["href"]
                q = self.session.query(Victim).filter_by(
                    name=victim_name, site=self.site)

                if q.count() == 0:
                    # new victim
                    r = p.get(victim_leak_site, headers=self.headers)
                    soup1 = BeautifulSoup(r.content.decode(), "html.parser")

                    description = soup1.find("p").text.strip()
                    if "Due to the fact that the Tor network is abandoning the second version and all domains will be abolished in September or October, we are moving to a new address" in description:
                        description = soup1.find_all("p")[1].text.strip()
                    
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
            self.session.commit()

        self.site.last_scraped = datetime.utcnow()

        # just for good measure
        self.session.commit()
