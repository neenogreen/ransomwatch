import logging
import socket
import time
from typing import Union

from stem import Signal
from stem.control import Controller
from stem.util.log import get_logger

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.firefox.firefox_binary import FirefoxBinary

from config import Config

class HeadlessBrowser:
    controller: Union[Controller, None]
    ip: str
    hostname: str
    socks_port: int
    ctrl_port: int
    password: str
    DRIVER = None

    def __init__(self):
        self.hostname = Config["proxy"]["hostname"]
        self.socks_port = Config["proxy"]["socks_port"]
        self.ctrl_port = Config["proxy"]["control_port"]
        self.password = Config["proxy"]["password"]
        self.controller = None
        self.ip = ""

        FIREFOX_BINARY = FirefoxBinary('/opt/firefox/firefox')
        PROFILE = webdriver.FirefoxProfile()
        PROFILE.set_preference("browser.cache.disk.enable", False)
        PROFILE.set_preference("browser.cache.memory.enable", False)
        PROFILE.set_preference("browser.cache.offline.enable", False)
        PROFILE.set_preference("network.http.use-cache", False)
        PROFILE.set_preference("general.useragent.override","Mozilla/5.0 (Windows NT 10.0; rv:91.0) Gecko/20100101 Firefox/91.0")
        PROFILE.set_preference('network.proxy.type', 1)
        PROFILE.set_preference('network.proxy.socks', self.hostname)
        PROFILE.set_preference('network.proxy.socks_port', self.socks_port)
        PROFILE.set_preference("network.proxy.socks_remote_dns", True)
        FIREFOX_OPTS = Options()
        FIREFOX_OPTS.log.level = "trace"
        FIREFOX_OPTS.headless = True
        GECKODRIVER_LOG = '/geckodriver.log'

        self.DRIVER = webdriver.Firefox(firefox_binary=FIREFOX_BINARY,
                firefox_profile=PROFILE,
                options=FIREFOX_OPTS,
                service_log_path=GECKODRIVER_LOG)

        logger = get_logger()
        logger.level = logging.WARNING
    
    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, *args):
        self.close()

    def connect(self) -> None:
        # get the IP of the proxy container
        # stem doesn't support connecting using the hostname for some reason
        self.ip = socket.gethostbyname(self.hostname)

        # connect to tor control port
        self.controller = Controller.from_port(address = self.ip, port = self.ctrl_port)

        # auth to control
        self.controller.authenticate(password = self.password)

    def close(self) -> None:
        assert(self.controller is not None)
        assert(self.DRIVER is not None)

        self.DRIVER.close()
        self.controller.close()

    def reconnect(self) -> None:
        assert(self.controller is not None)

        self.controller.close()

        # connect to tor control port
        self.controller = Controller.from_port(address = self.ip, port = self.ctrl_port)

        # auth to control
        self.controller.authenticate(password = self.password)

    def new_identity(self) -> None:
        assert(self.controller is not None)

        # request new identity
        self.controller.signal(Signal.NEWNYM)

        # wait for circuit to be established
        time.sleep(self.controller.get_newnym_wait())

    def res(self):
        return self.DRIVER.page_source

    def get(self, *args, **kwargs):
        self.DRIVER.get(*args, **kwargs)

    def find_element_by_class(self, name):
        return self.DRIVER.find_element(By.CLASS_NAME, name)

    def find_element_by_name(self, name):
        return self.DRIVER.find_element(By.NAME, name)
