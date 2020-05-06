import wx
from time import sleep
from common import xpath_class_predicate, HyperlinkDialog, FirefoxRunner
import threading
from selenium.webdriver.remote.webdriver import WebDriver

URL_AMAZON = r"https://www.amazon.com"
URL_FRESH_CART = r"https://www.amazon.com/cart/fresh"
XPATH_HELLO_USER = f"//a[@id='nav-link-accountList']/span[{xpath_class_predicate('nav-line-1')}]"
HELLO = "Hello, "
ID_CART = "nav-cart"
XPATH_CHECKOUT_FRESH_CART = r"//div[@id='sc-fresh-buy-box']//input[@type='submit']"
NAME_PROCEED_TO_CHECKOUT = "proceedToCheckout"
CLASSNAME_AVAILABILITY = "ufss-date-select-toggle-text-availability"
NOT_AVAILABLE = "Not available"
APP = wx.App()


class AmazonFresh(FirefoxRunner):
    def run_with(self, driver: WebDriver) -> None:
        print("Browsing to Amazon Fresh website...")
        driver.get(URL_AMAZON)
        print("Browser version: ")
        print(str(driver.capabilities["version"]))

        print("Verifying account logged in...")
        if not driver.find_element_by_xpath(XPATH_HELLO_USER).text.startswith(HELLO):
            with wx.MessageBox("Firefox automation profile not logged into Amazon... exiting.", "Amazon Fresh",
                               wx.OK | wx.ICON_ERROR) as dlg:
                dlg.ShowModal()
            return

        print("Opening Amazon Fresh cart...")
        driver.find_element_by_id(ID_CART).click()
        driver.find_element_by_xpath(XPATH_CHECKOUT_FRESH_CART).click()
        continue_buttons = driver.find_elements_by_name(NAME_PROCEED_TO_CHECKOUT)
        if continue_buttons:
            continue_buttons[0].click()

        print("Waiting for delivery time to be available...")
        num_tries = 0
        while not self.killed:
            for availability in driver.find_elements_by_class_name(CLASSNAME_AVAILABILITY):
                if NOT_AVAILABLE != availability.text:
                    with HyperlinkDialog("Checkout time available!", title="Amazon Fresh",
                                         label="Open Amazon Fresh cart", url=URL_FRESH_CART,
                                         style=wx.DEFAULT_DIALOG_STYLE | wx.STAY_ON_TOP) as dlg:
                        dlg.ShowModal()
                    self.killed = True
                    break
            if self.killed:
                break
            num_tries += 1
            if num_tries % 5 == 0:
                print(f"  Checked {num_tries} times.")
            sleep(15)
            if self.killed:
                break
            driver.refresh()


if __name__ == "__main__":
    try:
        AmazonFresh().run()
    except Exception as e:
        print(str(e))
        input("Press ENTER to continue...")

