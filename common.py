import subprocess
import os
import re
import sys
from time import sleep
from selenium import webdriver
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.common.proxy import Proxy
from selenium.webdriver.support.ui import WebDriverWait
import selenium.webdriver.support.expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from browsermobproxy import Server
import threading
from wx import CommandEvent, StaticText, Button, ArtProvider, Icon, ART_INFORMATION, ART_MESSAGE_BOX, EVT_BUTTON, \
    LaunchDefaultBrowser
from wx.adv import HyperlinkEvent, HyperlinkCtrl, EVT_HYPERLINK
from wx.lib.sized_controls import SizedDialog

DRIVER_EXE = r"C:\Users\Joe\Downloads\geckodriver-v0.26.0-win64\geckodriver.exe"
FIREFOX_PROFILE = r"C:\Users\Joe\AppData\Roaming\Mozilla\Firefox\Profiles\r7dltl7t.automation"
BROWSERMOB_PROXY = r"C:\Users\Joe\Downloads\browsermob-proxy-2.1.4-bin\browsermob-proxy-2.1.4\bin\browsermob-proxy.bat"


def xpath_class_predicate(cls: str) -> str:
    return f"contains(concat(' ',normalize-space(@class),' '),' {cls} ')"


class FirefoxRunner:
    def __init__(self, headless: bool = True) -> None:
        self.killed = False
        self.headless = headless

    def run(self) -> None:
        threading.Thread(target=self._listen_for_exit_signal, daemon=True).start()
        options = webdriver.FirefoxOptions()
        options.headless = self.headless
        profile = webdriver.FirefoxProfile(FIREFOX_PROFILE)

        with webdriver.Firefox(executable_path=DRIVER_EXE, firefox_profile=profile, options=options) as driver:
            self.run_with(driver)
        print("Done.")

    def run_with(self, driver: WebDriver) -> None:
        """Abstract method."""
        pass

    def _listen_for_exit_signal(self) -> None:
        while not self.killed:
            exit_signal = input("Type \"exit\" anytime to end program.\n\n")
            if exit_signal == "exit":
                print("Attempting graceful shutdown... ", end="", flush=True)
                self.killed = True


class ProxyFirefoxRunner(FirefoxRunner):
    def __init__(self, headless: bool = True):
        super().__init__(headless=headless)
        ProxyFirefoxRunner._force_shutdown_of_browsermob_proxy()
        sleep(1)
        self.proxy_server = Server(BROWSERMOB_PROXY)
        self.proxy_server.start()
        sleep(1)
        self.proxy_client = self.proxy_server.create_proxy()
        sleep(1)

    def run(self):
        threading.Thread(target=self._listen_for_exit_signal, daemon=True).start()
        options = webdriver.FirefoxOptions()
        options.headless = self.headless
        profile = webdriver.FirefoxProfile(FIREFOX_PROFILE)
        proxy = self.proxy_client.selenium_proxy()
        profile.set_proxy(proxy)        # required since running with preexisting profile
        # with webdriver.Firefox(executable_path=DRIVER_EXE, firefox_profile=profile, options=options, proxy=proxy) \
        with webdriver.Firefox(executable_path=DRIVER_EXE, firefox_profile=profile, options=options, proxy=proxy) as driver:
            try:
                self.run_with(driver)
            finally:
                self.proxy_server.stop()

    @staticmethod
    def _force_shutdown_of_browsermob_proxy() -> None:
        print("Checking for stale instances of browsermob-proxy...")
        if not sys.platform.startswith("win32"):
            raise Exception("Only implemented for Windows.")
        # jps is a JDK utility which lists the running Java processes
        result = subprocess.run(['jps', '-lv'], stdout=subprocess.PIPE).stdout.decode("utf-8")
        pattern = re.compile(r"(\d+)\s+(.*)")
        for line in result.splitlines():
            if "browsermob-proxy" in line:
                os.system(f"taskkill /f /pid {pattern.match(line).group(1)}")


def is_visible(driver: WebDriver, by: By, locator: str, timeout: int = 5):
    try:
        WebDriverWait(driver, timeout).until(EC.visibility_of_element_located((by, locator)))
        return True
    except TimeoutException as e:
        print(f"[TIMEOUT] {str(e)}")
        return False


def is_not_visible(driver: WebDriver, by: By, locator: str, timeout: int = 5):
    try:
        WebDriverWait(driver, timeout).until_not(EC.visibility_of_element_located((by, locator)))
        return True
    except TimeoutException as e:
        print(f"[TIMEOUT] {str(e)}")
        return False


def get_safe_filename(filename: str):
    keep_characters = (' ', '.', '_')
    return "".join(c for c in filename if c.isalnum() or c in keep_characters).rstrip()


class HyperlinkDialog(SizedDialog):
    """A dialog with a message, hyperlink, and OK button."""

    def __init__(self, message: str, label: str = None, url: str = None, **kwargs) -> None:
        super(HyperlinkDialog, self).__init__(parent=None, **kwargs)
        pane = self.GetContentsPane()

        text_ctrl = StaticText(pane, label=message)
        text_ctrl.SetFocus()
        text_ctrl.SetSizerProps(align="center")

        if url is not None:
            if label is None:
                label = url
            hyperlink = HyperlinkCtrl(pane, label=label, url=url)
            hyperlink.Bind(EVT_HYPERLINK, self.on_hyperlink)

        button_ok = Button(pane, label="OK")
        button_ok.Bind(EVT_BUTTON, self.on_ok)
        button_ok.SetSizerProps(align="center", border=(["top"], 10))

        self.SetIcon(Icon(ArtProvider.GetBitmap(ART_INFORMATION, ART_MESSAGE_BOX)))
        self.Fit()
        self.Centre()

    def on_hyperlink(self, event: HyperlinkEvent) -> None:
        LaunchDefaultBrowser(event.GetURL())
        self.Close()

    def on_ok(self, event: CommandEvent) -> None:
        self.Close()
