import wx
from time import sleep
from common import xpath_class_predicate, HyperlinkDialog, FirefoxRunner
from selenium.webdriver.remote.webdriver import WebDriver


URL_PRIMENOW = r"https://primenow.amazon.com/"
XPATH_PRIMENOW_CART = r"//a[@aria-label='Cart']/.."
XPATH_PRIMENOW_HELLO_USER = r"//a[@href='/account/address']/div[1]"
XPATH_PRIMENOW_PROCEED_TO_CHECKOUT = f"//span[{xpath_class_predicate('cart-checkout-button')}]//a[1]"
XPATH_PRIMENOW_NOT_AVAILABLE = r"//div[@id='delivery-slot']//span[contains(text(), 'No delivery windows available')]"
APP = wx.App()


class AmazonPrimeNow(FirefoxRunner):
    def run_with(self, driver: WebDriver) -> None:
        print("Browsing to Amazon PrimeNow website...")
        driver.get(URL_PRIMENOW)

        print("Verifying account logged in...")
        if not driver.find_elements_by_xpath(XPATH_PRIMENOW_HELLO_USER):
            with wx.MessageBox("Firefox automation profile not logged into Amazon... exiting.", "Amazon PrimeNow",
                               wx.OK | wx.ICON_ERROR) as dlg:
                dlg.ShowModal()
            return

        print("Opening Amazon PrimeNow cart...")
        driver.find_element_by_xpath(XPATH_PRIMENOW_CART).click()
        driver.find_element_by_xpath(XPATH_PRIMENOW_PROCEED_TO_CHECKOUT).click()

        print("Waiting for delivery time to be available...")
        num_tries = 0
        while not self.killed:
            if not driver.find_elements_by_xpath(XPATH_PRIMENOW_NOT_AVAILABLE):
                with HyperlinkDialog("Checkout time available!", title="Amazon PrimeNow",
                                     label="Open Amazon PrimeNow cart", url=URL_PRIMENOW,
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
        AmazonPrimeNow().run()
    except Exception as e:
        print(str(e))
        input("Press ENTER to continue...")

