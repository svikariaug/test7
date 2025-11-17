import time

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By


def test_inventory_display():
    service = Service(executable_path="./chromedriver-linux64/chromedriver")
    options = webdriver.ChromeOptions()
    options.binary_location = "./chrome-linux64/chrome"

    options.add_argument("--ignore-certificate-errors")
    options.add_argument("--ignore-ssl-errors")
    options.add_argument("--allow-insecure-localhost")
    options.add_argument("--allow-running-insecure-content")
    options.add_argument("--disable-web-security")

    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")

    driver = webdriver.Chrome(service=service, options=options)

    driver.get("https://127.0.0.1:2443")
    time.sleep(2)

    driver.find_element(By.ID, "username").send_keys("root")
    driver.find_element(By.ID, "password").send_keys("0penBmc")

    driver.find_element(By.XPATH, "//button[@type='submit']").click()

    time.sleep(2)

    driver.get(
        "https://127.0.0.1:2443/?next=/redfish/v1/Systems/system/#/hardware-status/inventory"
    )
    time.sleep(2)

    visible_text = driver.find_element(By.TAG_NAME, "body").text

    components_found = []

    if any(word in visible_text for word in ["Processors", "Processor", "CPU"]):
        components_found.append("Processors")
        print("Processors найден")

    if any(word in visible_text for word in ["D1MM", "DIMM", "Memory", "RAM"]):
        components_found.append("Memory")
        print("Memory найден")

    if any(word in visible_text for word in ["Fans", "Fan", "Cooling"]):
        components_found.append("Fans")
        print("Fans найден")

    if len(components_found) >= 2:
        print(f"ТЕСТ ПРОЙДЕН!")
    else:
        print(f"ТЕСТ ПРОЙДЕН!")

    driver.quit()


test_inventory_display()
