"""Drives the real UI in Chromium. usage: python e2e/test_ui_selenium.py <app-url> <selenium-url> [screenshot-dir]"""
import sys

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait

app_url, selenium_url = sys.argv[1], sys.argv[2]
shots = sys.argv[3] if len(sys.argv) > 3 else None

options = webdriver.ChromeOptions()
options.add_argument("--window-size=900,600")
driver = webdriver.Remote(command_executor=selenium_url, options=options)


def result_contains(expected):
    return lambda d: expected in d.find_element(By.ID, "result").text


try:
    driver.get(f"{app_url}/ui")
    assert driver.title == "Text Stats"
    print("PASS page title is 'Text Stats'")

    driver.find_element(By.ID, "text").send_keys("ship it ship it ship")
    driver.find_element(By.ID, "analyse").click()
    WebDriverWait(driver, 5).until(result_contains("5 words, 2 unique, 20 characters"))
    print("PASS analyse shows '5 words, 2 unique, 20 characters'")
    if shots:
        driver.save_screenshot(f"{shots}/q6-selenium-analyse.png")

    driver.find_element(By.ID, "top").click()
    WebDriverWait(driver, 5).until(result_contains("ship (3), it (2)"))
    print("PASS top words shows 'ship (3), it (2)' with the flag on")
    if shots:
        driver.save_screenshot(f"{shots}/q6-selenium-top-words.png")
finally:
    driver.quit()
print("All browser checks passed")
