pipeline {
    agent any

    environment {
        CHROME_VERSION = "131.0.6778.85"
        CHROMEDRIVER_VERSION = "131.0.6778.85"
    }

    stages {
        stage('Подготовка окружения (Python + Chrome + Chromedriver)') {
            steps {
                sh '''
                    set -e

                    echo "=== Установка Python 3 и зависимостей ==="
                    if ! command -v python3 >/dev/null 2>&1; then
                        if [ -f /etc/debian_version ]; then
                            apt-get update && apt-get install -y python3 python3-pip wget unzip
                        elif [ -f /etc/redhat-release ] || [ -f /etc/centos-release ]; then
                            yum install -y python3 python3-pip wget unzip || dnf install -y python3 python3-pip wget unzip
                        else
                            echo "Неизвестный дистрибутив"
                            exit 1
                        fi
                    fi

                    python3 -m pip install --upgrade pip
                    python3 -m pip install requests selenium --break-system-packages 2>/dev/null || python3 -m pip install requests selenium

                    echo "=== Скачивание Chrome ==="
                    [ -f chrome-linux64/chrome ] || (
                        wget -q https://storage.googleapis.com/chrome-for-testing-public/${CHROME_VERSION}/linux64/chrome-linux64.zip &&
                        unzip -q chrome-linux64.zip &&
                        chmod +x chrome-linux64/chrome
                    )

                    echo "=== Скачивание Chromedriver ==="
                    [ -f chromedriver-linux64/chromedriver ] || (
                        wget -q https://storage.googleapis.com/chrome-for-testing-public/${CHROMEDRIVER_VERSION}/linux64/chromedriver-linux64.zip &&
                        unzip -q chromedriver-linux64.zip &&
                        mv chromedriver-linux64/chromedriver chromedriver-linux64/ &&
                        chmod +x chromedriver-linux64/chromedriver
                    )

                    echo "=== Окружение готово ==="
                    python3 --version
                    ./chrome-linux64/chrome --version || true
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
r = requests.post(url, json={"UserName":"root","Password":"0penBmc"}, verify=False, timeout=10)
print(f"Статус: {r.status_code}")
if r.status_code != 201:
    print("Ошибка аутентификации!")
    print(r.text)
    sys.exit(1)
print("Redfish аутентификация УСПЕШНА")
PY
                '''
            }
        }

        stage('Redfish: Получение информации о системе') {
            steps {
                sh '''
                    python3 - <<'PY'
import requests, sys
s = requests.post("https://127.0.0.1:2443/redfish/v1/SessionService/Sessions",
                  json={"UserName":"root","Password":"0penBmc"}, verify=False)
token = s.headers["X-Auth-Token"]
headers = {"X-Auth-Token": token}
r = requests.get("https://127.0.0.1:2443/redfish/v1/Systems/system", headers=headers, verify=False)
if r.status_code != 200:
    print("Ошибка получения System info")
    sys.exit(1)
data = r.json()
print(f"PowerState: {data.get('PowerState')}")
print(f"Health: {data.get('Status',{}).get('Health')}")
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
headers = {"X-Auth-Token": token, "Content-Type": "application/json"}

# Power On
r = requests.post("https://127.0.0.1:2443/redfish/v1/Systems/system/Actions/ComputerSystem.Reset",
                  json={"ResetType": "On"}, headers=headers, verify=False)
print(f"PowerOn статус: {r.status_code}")

time.sleep(8)
state = requests.get("https://127.0.0.1:2443/redfish/v1/Systems/system", headers=headers, verify=False).json()
print(f"Новое состояние: {state.get('PowerState')}")
if state.get('PowerState') == "On":
    print("СЕРВЕР ВКЛЮЧЁН УСПЕШНО")
else:
    print("Сервер не включился")
PY
                '''
            }
        }

        stage('WebUI Selenium: Inventory') {
            steps {
                sh '''
                    python3 - <<'PY'
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
import time, sys

options = webdriver.ChromeOptions()
options.binary_location = "./chrome-linux64/chrome"
for a in ["--no-sandbox","--disable-dev-shm-usage","--disable-gpu","--ignore-certificate-errors","--ignore-ssl-errors","--allow-insecure-localhost","--disable-web-security"]:
    options.add_argument(a)

driver = webdriver.Chrome(service=Service("./chromedriver-linux64/chromedriver"), options=options)

driver.get("https://127.0.0.1:2443")
time.sleep(3)
driver.find_element(By.ID, "username").send_keys("root")
driver.find_element(By.ID, "password").send_keys("0penBmc")
driver.find_element(By.XPATH, "//button[@type='submit']").click()
time.sleep(4)

driver.get("https://127.0.0.1:2443/?next=/redfish/v1/Systems/system/#/hardware-status/inventory")
time.sleep(5)

text = driver.find_element(By.TAG_NAME, "body").text
found = sum(1 for kw in ["Processor","CPU","DIMM","Memory","Fan"] if kw in text)
print(f"Найдено компонентов: {found}/3")
if found >= 2:
    print("ТЕСТ INVENTORY ПРОЙДЕН")
else:
    print("ТЕСТ INVENTORY ПРОВАЛЕН")
    sys.exit(1)
driver.quit()
PY
                '''
            }
        }

        stage('WebUI Selenium: Sensors') {
            steps {
                sh '''
                    python3 - <<'PY'
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
import time, sys

options = webdriver.ChromeOptions()
options.binary_location = "./chrome-linux64/chrome"
for a in ["--no-sandbox","--disable-dev-shm-usage","--disable-gpu","--ignore-certificate-errors","--ignore-ssl-errors","--allow-insecure-localhost","--disable-web-security"]:
    options.add_argument(a)

driver = webdriver.Chrome(service=Service("./chromedriver-linux64/chromedriver"), options=options)
driver.get("https://127.0.0.1:2443")
time.sleep(3)
driver.find_element(By.ID, "username").send_keys("root")
driver.find_element(By.ID, "password").send_keys("0penBmc")
driver.find_element(By.XPATH, "//button[@type='submit']").click()
time.sleep(4)

driver.get("https://127.0.0.1:2443/?next=/redfish/v1/Systems/system/#/hardware-status/sensors")
time.sleep(5)

if "Sensor" in driver.find_element(By.TAG_NAME, "body").text:
    print("ТЕСТ SENSORS ПРОЙДЕН")
else:
    print("ТЕСТ SENSORS ПРОВАЛЕН")
    sys.exit(1)
driver.quit()
PY
                '''
            }
        }
    }

    post {
        always {
            archiveArtifacts artifacts: '*.log', allowEmptyArchive: true
            cleanWs()
        }
        success { echo "ВСЁ ПРОШЛО УСПЕШНО!" }
        failure { echo "ГДЕ-ТО УПАЛО" }
    }
}
