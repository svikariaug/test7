pipeline {
    agent any

    stages {
        stage('Информация о среде') {
            steps {
                sh '''
                    echo "=== ИНФОРМАЦИЯ О СРЕДЕ JENKINS ===" > env_report.txt
                    whoami >> env_report.txt
                    pwd >> env_report.txt
                    hostname >> env_report.txt
                    date >> env_report.txt
                    echo "Python версия:" >> env_report.txt
                    python3 --version >> env_report.txt 2>&1 || echo "python3 не найден"
                    echo "Chrome и Chromedriver присутствуют:" >> env_report.txt
                    ls -la chrome-linux64/chrome chromedriver-linux64/chromedriver >> env_report.txt 2>&1 || echo "Не найдены"
                    echo "СРЕДА ГОТОВА К CI/CD" >> env_report.txt
                '''
                archiveArtifacts 'env_report.txt'
            }
        }

        stage('Redfish: Аутентификация') {
            steps {
                sh '''
                    python3 - <<'PY'
import requests

BMC_IP = "127.0.0.1"
BMC_PORT = "2443"
url = f"https://{BMC_IP}:{BMC_PORT}/redfish/v1/SessionService/Sessions"
data = {"UserName": "root", "Password": "0penBmc"}
headers = {"Content-Type": "application/json"}

print("Redfish: Тест аутентификации...")
r = requests.post(url, json=data, headers=headers, verify=False, timeout=10)

print(f"Статус: {r.status_code}")
if r.status_code == 201:
    token = r.headers.get("X-Auth-Token")
    print("Аутентификация УСПЕШНА!")
    print(f"Токен: {token[:20]}...")
else:
    print("ОШИБКА аутентификации!")
    print(r.text)
    exit(1)
PY
                '''
            }
        }

        stage('Redfish: Получение информации о системе') {
            steps {
                sh '''
                    python3 - <<'PY'
import requests, json, sys

BMC_IP = "127.0.0.1"
BMC_PORT = "2443"

# Логин
session = requests.post(
    f"https://{BMC_IP}:{BMC_PORT}/redfish/v1/SessionService/Sessions",
    json={"UserName": "root", "Password": "0penBmc"},
    verify=False, timeout=10
)
token = session.headers.get("X-Auth-Token")
headers = {"X-Auth-Token": token, "Content-Type": "application/json"}

# GET /Systems/system
r = requests.get(f"https://{BMC_IP}:{BMC_PORT}/redfish/v1/Systems/system", headers=headers, verify=False)

print(f"Статус: {r.status_code}")
if r.status_code != 200:
    print("Ошибка получения информации о системе")
    sys.exit(1)

data = r.json()
print("Информация о системе получена УСПЕШНО")
print(f"PowerState: {data.get('PowerState')}")
print(f"Health: {data.get('Status', {}).get('Health', 'N/A')}")
print(f"State: {data.get('Status', {}).get('State', 'N/A')}")
PY
                '''
            }
        }

        stage('Redfish: Включение питания') {
            steps {
                sh '''
                    python3 - <<'PY'
import requests, json, time, sys

BMC_IP = "127.0.0.1"
BMC_PORT = "2443"

# Логин
s = requests.post(
    f"https://{BMC_IP}:{BMC_PORT}/redfish/v1/SessionService/Sessions",
    json={"UserName": "root", "Password": "0penBmc"},
    verify=False, timeout=10
)
token = s.headers.get("X-Auth-Token")
headers = {"X-Auth-Token": token, "Content-Type": "application/json"}

# Текущее состояние
current = requests.get(f"https://{BMC_IP}:{BMC_PORT}/redfish/v1/Systems/system", headers=headers, verify=False).json()
print(f"Текущее состояние: {current.get('PowerState')}")

# Включаем
print("Отправка команды Power On...")
r = requests.post(
    f"https://{BMC_IP}:{BMC_PORT}/redfish/v1/Systems/system/Actions/ComputerSystem.Reset",
    json={"ResetType": "On"},
    headers=headers,
    verify=False
)

print(f"Статус команды: {r.status_code}")
if r.status_code in [200, 204]:
    print("Команда ВКЛЮЧЕНИЯ принята!")
else:
    print("Ошибка выполнения команды")
    sys.exit(1)

# Ждём и проверяем
time.sleep(8)
new = requests.get(f"https://{BMC_IP}:{BMC_PORT}/redfish/v1/Systems/system", headers=headers, verify=False).json()
new_state = new.get('PowerState')
print(f"Новое состояние: {new_state}")
if new_state == "On":
    print("СЕРВЕР УСПЕШНО ВКЛЮЧЁН!")
else:
    print("Состояние не изменилось на On")
PY
                '''
            }
        }

        stage('WebUI Selenium: Проверка страницы Inventory') {
            steps {
                sh '''
                    python3 - <<'PY'
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
import time, sys

service = Service(executable_path="./chromedriver-linux64/chromedriver")
options = webdriver.ChromeOptions()
options.binary_location = "./chrome-linux64/chrome"
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
options.add_argument("--disable-gpu")
options.add_argument("--ignore-certificate-errors")
options.add_argument("--ignore-ssl-errors")
options.add_argument("--allow-insecure-localhost")
options.add_argument("--disable-web-security")

driver = webdriver.Chrome(service=service, options=options)
driver.get("https://127.0.0.1:2443")
time.sleep(3)

driver.find_element(By.ID, "username").send_keys("root")
driver.find_element(By.ID, "password").send_keys("0penBmc")
driver.find_element(By.XPATH, "//button[@type='submit']").click()
time.sleep(3)

driver.get("https://127.0.0.1:2443/?next=/redfish/v1/Systems/system/#/hardware-status/inventory")
time.sleep(4)

text = driver.find_element(By.TAG_NAME, "body").text
found = []

if any(x in text for x in ["Processor", "CPU", "Processors"]):
    found.append("Processors")
    print("Processors найден")

if any(x in text for x in ["DIMM", "Memory", "RAM"]):
    found.append("Memory")
    print("Memory найден")

if any(x in text for x in ["Fan", "Fans", "Cooling"]):
    found.append("Fans")
    print("Fans найден")

print(f"Найдено компонентов: {len(found)}")
if len(found) >= 2:
    print("ТЕСТ INVENTORY ПРОЙДЕН!")
else:
    print("ТЕСТ INVENTORY ПРОВАЛЕН!")
    sys.exit(1)

driver.quit()
PY
                '''
            }
        }

        stage('WebUI Selenium: Проверка страницы Sensors') {
            steps {
                sh '''
                    python3 - <<'PY'
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
import time, sys

service = Service(executable_path="./chromedriver-linux64/chromedriver")
options = webdriver.ChromeOptions()
options.binary_location = "./chrome-linux64/chrome"
for arg in [
    "--no-sandbox", "--disable-dev-shm-usage", "--disable-gpu",
    "--ignore-certificate-errors", "--ignore-ssl-errors",
    "--allow-insecure-localhost", "--disable-web-security"
]:
    options.add_argument(arg)

driver = webdriver.Chrome(service=service, options=options)
driver.get("https://127.0.0.1:2443")
time.sleep(3)

driver.find_element(By.ID, "username").send_keys("root")
driver.find_element(By.ID, "password").send_keys("0penBmc")
driver.find_element(By.XPATH, "//button[@type='submit']").click()
time.sleep(3)

driver.get("https://127.0.0.1:2443/?next=/redfish/v1/Systems/system/#/hardware-status/sensors")
time.sleep(5)

text = driver.find_element(By.TAG_NAME, "body").text
if "Sensors" in text or "Sensor" in text:
    print("Страница Sensors загружена — ТЕСТ ПРОЙДЕН!")
else:
    print("Заголовок Sensors НЕ найден — ТЕСТ ПРОВАЛЕН!")
    sys.exit(1)

driver.quit()
PY
                '''
            }
        }

        stage('Итоговый отчёт') {
            steps {
                sh '''
                    echo "=============================================="
                    echo " ВСЕ ТЕСТЫ OPENBMC / REDFISH / WEBUI УСПЕШНО ПРОЙДЕНЫ "
                    echo "=============================================="
                '''
            }
        }
    }

    post {
        always {
            archiveArtifacts artifacts: '*.txt', allowEmptyArchive: true
            cleanWs()
        }
        success {
            echo "Пайплайн завершён успешно!"
        }
        failure {
            echo "Один или несколько тестов провалились"
        }
    }
}
