from datetime import datetime
import logging
import re
import json
import html2text

from db.models import Victim
from net.proxy import Proxy
from .sitecrawler import SiteCrawler

class NoEscape(SiteCrawler):
    actor = "NoEscape"

    def _handle_page(self, body: str):
        tmp = json.loads(body)
        victim_list = tmp["newcomers"]
        victim_list += tmp["archive"]

        for victim in victim_list:
            victim_name = victim["company_name"]
            victim_leak_site = self.url + "/post/" + victim["id"]
            description = "Website: " + victim["title"] + "\n" + re.sub("\n", " ", html2text.html2text(victim["text"]))
            published_dt = datetime.strptime(victim["created_at"], "%d %b %Y")

            q = self.session.query(Victim).filter_by(
                url=victim_leak_site, site=self.site)

            if q.count() == 0:
                # new victim
                v = Victim(name=victim_name, url=victim_leak_site, published=published_dt, description=description,
                            first_seen=datetime.utcnow(), last_seen=datetime.utcnow(), site=self.site)
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
        self.init_scrape = True
        with Proxy() as p:
            hdr = self.headers.copy()
            hdr["Verify"] = "EsaymapRTc9JbqTHYcppgAJ8xHbX4Dxb"
            r = p.post(f"{self.url}/c9cc21dcd195ed51/f0a89ce8cbaea9b0/auth", headers=hdr)
            hdr["token"] = r.text.strip()
            r = p.post(f"{self.url}/c9cc21dcd195ed51/f0a89ce8cbaea9b0/posts", headers=hdr)
            self._handle_page(r.content.decode()) 
        self.site.last_scraped = datetime.utcnow()
