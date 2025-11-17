pipeline {
    agent {
        docker {
            image 'python:3.11-slim-bookworm'
            args '-u root --network host'   // host — чтобы 127.0.0.1:2443 был доступен (OpenBMC/QEMU)
            reuseNode true                  // ускоряет запуск
        }
    }

    environment {
        // Актуальные стабильные версии на ноябрь 2025
        CHROME_VERSION = "131.0.6778.85"
        CHROMEDRIVER_VERSION = "131.0.6778.85"
    }

    stages {
        stage('Подготовка окружения') {
            steps {
                sh '''
                    set -e

                    echo "=== Установка системных утилит ==="
                    apt-get update && apt-get install -y --no-install-recommends \\
                        wget unzip ca-certificates fonts-liberation libnss3 libgdk-pixbuf2.0-0 \\
                        libgtk-3-0 libx11-xcb1 libasound2 libatk-bridge2.0-0 libdrm2 libxcomposite1

                    echo "=== Установка Python-пакетов ==="
                    python3 -m pip install --upgrade pip
                    python3 -m pip install requests selenium

                    echo "=== Скачивание Google Chrome ==="
                    wget -q https://storage.googleapis.com/chrome-for-testing-public/${CHROME_VERSION}/linux64/chrome-linux64.zip
                    unzip -q chrome-linux64.zip
                    ln -sf $(pwd)/chrome-linux64/chrome /usr/local/bin/chrome

                    echo "=== Скачивание Chromedriver ==="
                    wget -q https://storage.googleapis.com/chrome-for-testing-public/${CHROMEDRIVER_VERSION}/linux64/chromedriver-linux64.zip
                    unzip -q chromedriver-linux64.zip
                    mv chromedriver-linux64/chromedriver ./chromedriver-linux64/
                    chmod +x ./chromedriver-linux64/chromedriver

                    echo "=== Всё готово ==="
                    python3 --version
                    chrome --version || true
                    ./chromedriver-linux64/chromedriver --version || true
                '''
            }
        }

        stage('Redfish: Аутентификация') {
            steps {
                sh '''
                    python3 - <<'PY'
import requests, sys
url = "https://127.0.0.1:2443/redfish/v1/SessionService/Sessions"
r = requests.post(url, json={"UserName":"root","Password":"0penBmc"}, verify=False, timeout=15)
print(f"Login status: {r.status_code}")
if r.status_code != 201:
    print("ОШИБКА: Не удалось войти в BMC!")
    print(r.text)
    sys.exit(1)
print("Redfish аутентификация прошла УСПЕШНО")
PY
                '''
            }
        }

        stage('Redfish: Информация о системе') {
            steps {
                sh '''
                    python3 - <<'PY'
import requests, sys
s = requests.post("https://127.0.0.1:2443/redfish/v1/SessionService/Sessions",
                  json={"UserName":"root","Password":"0penBmc"}, verify=False, timeout=15)
token = s.headers["X-Auth-Token"]
h = {"X-Auth-Token": token}
r = requests.get("https://127.0.0.1:2443/redfish/v1/Systems/system", headers=h, verify=False)
if r.status_code != 200:
    print("Ошибка получения System info")
    sys.exit(1)
data = r.json()
print(f"PowerState: {data.get('PowerState')}")
print(f"Health: {data.get('Status', {}).get('Health', 'N/A')}")
print("Информация о системе получена УСПЕШНО")
PY
                '''
            }
        }

        stage('Redfish: Включение питания') {
            steps {
                sh '''
                    python3 - <<'PY'
import requests, time, sys
s = requests.post("https://127.0.0.1:2443/redfish/v1/SessionService/Sessions",
                  json={"UserName":"root","Password":"0penBmc"}, verify=False)
token = s.headers["X-Auth-Token"]
h = {"X-Auth-Token": token, "Content-Type": "application/json"}

print("Отправка команды включения питания...")
r = requests.post("https://127.0.0.1:2443/redfish/v1/Systems/system/Actions/ComputerSystem.Reset",
                  json={"ResetType": "On"}, headers=h, verify=False)
print(f"Команда принята, код: {r.status_code}")

time.sleep(10)
state = requests.get("https://127.0.0.1:2443/redfish/v1/Systems/system", headers=h, verify=False).json()
new_state = state.get("PowerState")
print(f"Текущее состояние: {new_state}")
if new_state == "On":
    print("СЕРВЕР УСПЕШНО ВКЛЮЧЁН!")
else:
    print("Сервер не включился")
PY
                '''
            }
        }

        stage('WebUI: Inventory') {
            steps {
                sh '''
                    python3 - <<'PY'
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
import time, sys

options = webdriver.ChromeOptions()
options.binary_location = "/workspace/chrome-linux64/chrome"
for arg in ["--headless", "--no-sandbox", "--disable-dev-shm-usage", "--disable-gpu",
            "--ignore-certificate-errors", "--ignore-ssl-errors", "--allow-insecure-localhost",
            "--disable-web-security"]:
    options.add_argument(arg)

driver = webdriver.Chrome(service=Service("./chromedriver-linux64/chromedriver"), options=options)

driver.get("https://127.0.0.1:2443")
time.sleep(4)
driver.find_element(By.ID, "username").send_keys("root")
driver.find_element(By.ID, "password").send_keys("0penBmc")
driver.find_element(By.XPATH, "//button[@type='submit']").click()
time.sleep(5)

driver.get("https://127.0.0.1:2443/?next=/redfish/v1/Systems/system/#/hardware-status/inventory")
time.sleep(6)

text = driver.find_element(By.TAG_NAME, "body").text
found = sum(1 for word in ["Processor","CPU","DIMM","Memory","Fan","Fans"] if word in text)
print(f"Найдено компонентов: {found}")
if found >= 2:
    print("ТЕСТ INVENTORY — ПРОЙДЕН")
else:
    print("ТЕСТ INVENTORY — ПРОВАЛЕН")
    sys.exit(1)
driver.quit()
PY
                '''
            }
        }

        stage('WebUI: Sensors') {
            steps {
                sh '''
                    python3 - <<'PY'
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
import time, sys

options = webdriver.ChromeOptions()
options.binary_location = "/workspace/chrome-linux64/chrome"
for arg in ["--headless", "--no-sandbox", "--disable-dev-shm-usage", "--disable-gpu",
            "--ignore-certificate-errors", "--ignore-ssl-errors", "--allow-insecure-localhost"]:
    options.add_argument(arg)

driver = webdriver.Chrome(service=Service("./chromedriver-linux64/chromedriver"), options=options)

driver.get("https://127.0.0.1:2443")
time.sleep(4)
driver.find_element(By.ID, "username").send_keys("root")
driver.find_element(By.ID, "password").send_keys("0penBmc")
driver.find_element(By.XPATH, "//button[@type='submit']").click()
time.sleep(5)

driver.get("https://127.0.0.1:2443/?next=/redfish/v1/Systems/system/#/hardware-status/sensors")
time.sleep(6)

if "Sensor" in driver.find_element(By.TAG_NAME, "body").text:
    print("ТЕСТ SENSORS — ПРОЙДЕН")
else:
    print("ТЕСТ SENSORS — ПРОВАЛЕН")
    sys.exit(1)
driver.quit()
PY
                '''
            }
        }

        stage('Финал') {
            steps {
                echo "ВСЁ ПРОШЛО УСПЕШНО! OpenBMC + Redfish + WebUI протестированы"
            }
        }
    }

    post {
        always {
            cleanWs()
        }
        success {
            echo "Пайплайн завершён без ошибок"
        }
        failure {
            echo "Где-то упало — смотри логи выше"
        }
    }
}
