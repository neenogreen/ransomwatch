from datetime import datetime
import logging
from config import Config
from random import randint
from time import sleep

import json
import websocket

from db.models import Victim
from net.proxy import Proxy
from notifications.manager import NotificationManager
from .sitecrawler import SiteCrawler

class Blackbasta(SiteCrawler):
    actor = "Blackbasta"

    def is_site_up(self) -> bool:
        ws = websocket.WebSocket()
        try:
            ws.connect(f"ws{self.url[4:]}/ws",
                      http_proxy_host=Config["proxy"]["hostname"],
                      http_proxy_port=Config["proxy"]["socks_port"],
                      proxy_type="socks5h")
            ws.send("{\"name\":\"get_companies\"}")
            res = ws.recv()
            ws.close()
        except Exception:
            return False
        if res:
            return True
        return False
        
    def _handle_page(self, body: str):
        victim_list = json.loads(body)
        victim_list = victim_list["additional"]["Companies"]

        for victim in victim_list:
            victim_name = victim["title"]
            pub_data = victim["data_published"]
            victim_leak_site = self.url + "/?id=" + victim_name + "#" + str(pub_data)
            
            q = self.session.query(Victim).filter_by(
                name=victim_name, site=self.site)

            if q.count() == 0:
                # new victim
                v = Victim(name=victim_name, url=victim_leak_site,
                            published=datetime.utcnow(),
                            first_seen=datetime.utcnow(),
                            last_seen=datetime.utcnow(), site=self.site)
                self.session.add(v)
                self.new_victims.append(v)
            else:
                # already seen, update last_seen
                v = q.first()
                old_pub = int(v.url.split("#")[-1])
                v.last_seen = datetime.utcnow()
                v.url = victim_leak_site
                if pub_data != old_pub:
                    NotificationManager.send_new_victim_notification(v)
            # add the org to our seen list
            self.current_victims.append(v)
        self.session.commit()

    def scrape_victims(self):
        ws = websocket.WebSocket()
        ws.connect(f"ws{self.url[4:]}/ws",
                  http_proxy_host=Config["proxy"]["hostname"],
                  http_proxy_port=Config["proxy"]["socks_port"],
                  proxy_type="socks5h")
        ws.send("{\"name\":\"get_companies\"}")
        ws.recv()
        cnt = json.loads(ws.recv())
        cnt = cnt["additional"]["Pages"]

        for i in range(1, cnt+1):
            ws.send("{\"name\":\"get_companies\",\"additional\":"+str(i)+"}")
            self._handle_page(ws.recv())

        ws.close()
        self.site.last_scraped = datetime.utcnow()
