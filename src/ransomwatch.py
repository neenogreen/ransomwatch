import logging
import sys
import traceback

from config import Config
from notifications import NotificationManager
import sites
from net.proxy import Proxy

logging.basicConfig(
    format="%(asctime)s [%(levelname)s] %(message)s",
    level=logging.INFO,
    datefmt="%Y/%m/%d %H:%M:%S",
    handlers=[
        #logging.FileHandler(filename="enum.log", mode="a"),
        logging.StreamHandler()
    ]
)


def defang(u): return u.replace("http", "hxxp").replace(".onion", "[.]onion")


def main(argv):
    logging.info("Initializing")

    sites_to_analyze = [
        sites.Avaddon,
        sites.Blackbyte,
        sites.Conti,
        sites.DarkSide,
        sites.REvil,
        sites.Babuk,
        sites.Ranzy,
        sites.Astro,
        sites.Pay2Key,
        sites.Cuba,
        sites.RansomEXX,
        sites.Mount,
        sites.Ragnarok,
        sites.Ragnar,
        sites.Suncrypt,
        sites.Everest,
        sites.Nefilim,
        sites.Cl0p,
        sites.Pysa,
        sites.Hive,
        sites.Lockbit,
        sites.Xing,
        sites.Lorenz,
        sites.Cometa,
        sites.Arvin,
        sites.Blackmatter,
        sites.Avoslocker,
        sites.LV,
        sites.Marketo,
        sites.LockData,
        sites.Rook,
        sites.Alphv,
        sites.Blackbasta,
        sites.ViceSociety,
        sites.Royal,
        sites.Blacktor,
        sites.DarkLeakMarket,
        sites.Quantum,
        sites.DataLeak,
        sites.Omega,
        sites.Mallox,
        sites.Qilin,
        sites.Unsafe,
        sites.Play,
        sites.Bianlian,
        sites.Daixin,
        sites.Relic,
        sites.RansomHouse,
        sites.Nokoyawa,
        sites.Snatch,
        sites.Karakurt,
        sites.FreeCivilian,
        sites.Monti,
        sites.MoneyMessage,
        sites.Eightbase,
        sites.Donut,
        sites.Akira,
        sites.Abyss,
        sites.Cryptnet,
        sites.Malas,
        sites.Rancoz,
        sites.RaGroup,
        sites.MedusaRansomware,
        sites.BlackSuit,
        sites.Vendetta,
        sites.Dunghill,
        sites.Trigona,
        sites.MedusaLocker,
        sites.Cactus,
        sites.Rhysida,
        sites.NoEscape,
        sites.Cloak
    ]

    NotificationManager.send_info_notification(f"Starting: Found {len(sites_to_analyze)} sites")
    logging.info(f"Found {len(sites_to_analyze)} sites")

    with Proxy() as p:
        try:
            r = p.get("http://ifconfig.me/ip", timeout = 60)
            if r.status_code >= 400:
                logging.warning(f"The web service for public IP fetch is down")
            else:
                logging.info(f"Public Tor IP address: {r.text}")
        except Exception as e:
            logging.warning(f"The web service for public IP fetch can't be reached")

    for site in sites_to_analyze:
        logging.info(f"Starting process for {site.actor}")

        if site.actor.lower() not in Config["sites"]:
            logging.warning(f"No URL found in config for this actor, skipping")
            continue

        s = site(Config["sites"][site.actor.lower()])

        if not s.is_up:
            logging.warning(f"{site.actor} is down, notifying + skipping")
            NotificationManager.send_site_down_notification(s.site)
            continue

        if s.first_run:
            logging.info(
                f"This is the first scrape for {site.actor}, no victim notifications will be sent")

        logging.info(f"Scraping victims")
        try:
            s.scrape_victims()
        except:
            logging.error(
                f"Got an error while scraping {site.actor}, notifying")

            tb = traceback.format_exc()

            # send error notifications
            NotificationManager.send_error_notification(
                f"{site.actor} scraping", tb)

            # log exception
            logging.error(tb.strip())  # there is a trailing newline

        logging.info(f"There are {len(s.new_victims)} new victims")

        # send notifications for new victims
        if not s.first_run and len(s.new_victims) > 0:
            logging.info("Notifying for new victims")
            for v in s.new_victims:
                NotificationManager.send_new_victim_notification(v)
        elif s.first_run and len(s.new_victims) > 0 and s.init_scrape:
            # send notifications for old victims 
            logging.info("Notifying for old victims")
            for v in s.new_victims:
                if v.first_seen.date() == v.published.date():
                    v.first_seen = None
                else:
                    v.first_seen = v.published
                NotificationManager.send_new_victim_notification(v)

        logging.info(f"Identifying removed victims")
        removed = s.identify_removed_victims()
        logging.info(f"There are {len(removed)} removed victims")

        # send notifications for removed victims
        if not s.first_run and len(removed) > 0:
            logging.info("Notifying for removed victims")
            for v in removed:
                NotificationManager.send_victim_removed_notification(v)

        # close db session
        s.session.close()

        logging.info(f"Finished {site.actor}")

    NotificationManager.send_info_notification("Finished all sites, exiting")
    logging.info("Finished all sites, exiting")


if __name__ == "__main__":
    try:
        main(sys.argv)
    except:
        logging.error(f"Got a fatal error, notifying + aborting")

        tb = traceback.format_exc()

        # send slack error notifications
        NotificationManager.send_error_notification(
            f"Non-scraping failure", tb, fatal=True)

        # log exception
        logging.error(tb.strip())  # there is a trailing newline
