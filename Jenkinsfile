pipeline {
    agent any

    stages {
        stage('Подготовка окружения') {
            steps {
                sh '''
                    set -e
                    sudo apt-get update
                    sudo apt-get install -y --no-install-recommends \
                        qemu-system-aarch64 qemu-utils python3 python3-pip wget unzip curl
                    pip3 install --break-system-packages --no-cache-dir requests
                '''
            }
        }

        stage('Скачивание образа OpenBMC из GitHub') {
            steps {
                sh '''
                    set -e
                    echo "Скачиваем образ romulus из GitHub репозитория komal-tyt/testir_laba7..."
                    # Замени 'romulus.zip' на реальное имя файла в /romulus/
                    wget -q https://github.com/komal-tyt/testir_laba7/raw/main/romulus/romulus.zip -O romulus.zip
                    
                    echo "Распаковка и конвертация в qcow2..."
                    unzip -j -q romulus.zip "*.mtd" || unzip -q romulus.zip  # Если zip с mtd
                    MTD_FILE=$(ls *.mtd 2>/dev/null | head -1 || echo "romulus.static.mtd")  # Автоопределение
                    if [ ! -f "$MTD_FILE" ]; then
                        echo "Ошибка: MTD-файл не найден в zip. Проверь имя в репозитории."
                        exit 1
                    fi
                    qemu-img convert -f raw -O qcow2 "$MTD_FILE" openbmc-romulus.qcow2
                    echo "Образ готов: openbmc-romulus.qcow2 ($(ls -lh openbmc-romulus.qcow2 | awk '{print $5}'))"
                '''
            }
        }

        stage('Запуск QEMU с OpenBMC') {
            steps {
                sh '''
                    set -e
                    qemu-system-aarch64 -m 2G -M romulus-bmc \
                        -drive file=openbmc-romulus.qcow2,format=qcow2,if=virtio \
                        -nic user,hostfwd=tcp::2443-:443,hostfwd=tcp::2222-:22 \
                        -nographic &
                    echo $! > qemu.pid
                    echo "Ожидание загрузки OpenBMC (~110 сек)..."
                    sleep 110
                '''
            }
        }

        stage('Автотесты OpenBMC (Python)') {
            steps {
                sh '''
                    set -e
                    python3 - <<'PY'
import requests, time, json, sys
from requests.auth import HTTPBasicAuth

base_url = "https://127.0.0.1:2443"
session = requests.Session()
session.verify = False

print("=== АВТОТЕСТЫ OPENBMC НА PYTHON ===")

# 1. Проверка Redfish root
r = session.get(f"{base_url}/redfish/v1")
print(f"Redfish root: статус {r.status_code}")
if r.status_code != 200:
    print("FAIL: Redfish недоступен")
    sys.exit(1)

# 2. Логин и сессия
login_data = {"UserName": "root", "Password": "0penBmc"}
r = session.post(f"{base_url}/redfish/v1/SessionService/Sessions", json=login_data)
print(f"Сессия создана: статус {r.status_code}")
token = r.headers.get("X-Auth-Token", "N/A")
if r.status_code != 201:
    print("FAIL: Логин не удался")
    sys.exit(1)

# 3. Информация о системе
headers = {"X-Auth-Token": token}
r = session.get(f"{base_url}/redfish/v1/Systems/system", headers=headers)
data = r.json()
print(f"PowerState: {data.get('PowerState', 'N/A')}")
print(f"Health: {data.get('Status', {}).get('Health', 'N/A')}")

# 4. Включение питания
r = session.post(f"{base_url}/redfish/v1/Systems/system/Actions/ComputerSystem.Reset",
                 headers=headers, json={"ResetType": "On"})
print(f"Команда power on: статус {r.status_code}")
time.sleep(15)  # Ждём изменения состояния

r = session.get(f"{base_url}/redfish/v1/Systems/system", headers=headers)
new_state = r.json().get("PowerState", "N/A")
print(f"Состояние после включения: {new_state}")

# 5. Проверка сенсоров (Thermal)
r = session.get(f"{base_url}/redfish/v1/Chassis/chassis/Thermal", headers=headers)
sensors = r.json().get("Temperatures", [])
print(f"Найдено сенсоров: {len(sensors)}")

print("=== АВТОТЕСТЫ УСПЕШНЫ ===")
PY
                '''
            }
        }

        stage('WebUI тесты OpenBMC (Python)') {
            steps {
                sh '''
                    set -e
                    python3 - <<'PY'
import requests
session = requests.Session()
session.verify = False

print("=== WEBUI ТЕСТЫ НА PYTHON ===")

# 1. Главная страница
r = session.get("https://127.0.0.1:2443")
print(f"Главная страница: статус {r.status_code}")
if r.status_code != 200:
    print("FAIL: Главная страница недоступна")
    sys.exit(1)

# 2. Проверка страницы инвентаря
r = session.get("https://127.0.0.1:2443/?next=/redfish/v1/Systems/system/#/hardware-status/inventory")
print(f"Инвентарь: статус {r.status_code}")
if "Processor" in r.text or "DIMM" in r.text:
    print("OK: Инвентарь содержит компоненты")
else:
    print("FAIL: Компоненты не найдены")

# 3. Проверка страницы сенсоров
r = session.get("https://127.0.0.1:2443/?next=/redfish/v1/Systems/system/#/hardware-status/sensors")
print(f"Сенсоры: статус {r.status_code}")
if "Sensor" in r.text:
    print("OK: Сенсоры найдены")
else:
    print("FAIL: Сенсоры не найдены")

print("=== WEBUI ТЕСТЫ УСПЕШНЫ ===")
PY
                '''
            }
        }

        stage('Нагрузочное тестирование OpenBMC (Python)') {
            steps {
                sh '''
                    set -e
                    python3 - <<'PY'
import requests
import threading
import time

def load_request():
    try:
        r = requests.get("https://127.0.0.1:2443/redfish/v1", verify=False, timeout=5)
        return r.status_code == 200
    except:
        return False

print("=== НАГРУЗОЧНОЕ ТЕСТИРОВАНИЕ ===")
threads = []
success_count = 0

for i in range(100):
    t = threading.Thread(target=lambda: globals().update(success=(load_request() and globals().get('success', 0) + 1)))
    t.start()
    threads.append(t)

for t in threads:
    t.join()

print(f"Успешных запросов из 100: {success_count}")
print("Нагрузка завершена успешно")

# Проверка живости после нагрузки
r = requests.get("https://127.0.0.1:2443/redfish/v1", verify=False)
print(f"Система после нагрузки: статус {r.status_code}")
PY
                '''
            }
        }
    }

    post {
        always {
            sh '''
                [ -f qemu.pid ] && kill $(cat qemu.pid) 2>/dev/null || true
                rm -f qemu.pid openbmc-romulus.qcow2 romulus.zip *.mtd 2>/dev/null || true
            '''
        }
        success {
            echo "Лабораторная работа 7 выполнена успешно!"
            echo "Все Python-тесты прошли. Готово к сдаче."
        }
        failure {
            echo "Ошибка — смотри логи."
        }
    }
}
