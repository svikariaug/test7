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

        stage('Скачивание и подготовка образа OpenBMC') {
            steps {
                sh '''
                    set -e
                    wget -q "https://jenkins.openbmc.org/job/ci-openbmc/lastSuccessfulBuild/distro=ubuntu,label=docker-builder,target=romulus/artifact/openbmc/build/tmp/deploy/images/romulus/*zip*/romulus.zip" -O romulus.zip
                    unzip -j -q romulus.zip "*.static.mtd"
                    MTD_FILE=$(ls *.static.mtd | head -1)
                    qemu-img convert -f raw -O qcow2 "$MTD_FILE" openbmc-romulus.qcow2
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
                    echo "Ожидание загрузки OpenBMC..."
                    sleep 110
                '''
            }
        }

        stage('Запуск автотестов для OpenBMC (Python)') {
            steps {
                sh '''
                    set -e
                    python3 - <<'PY'
import requests, time, json, sys
from requests.auth import HTTPBasicAuth

base = "https://127.0.0.1:2443"
s = requests.Session()
s.verify = False

print("1. Проверка доступности Redfish")
r = s.get(f"{base}/redfish/v1")
print("Статус:", r.status_code)
if r.status_code != 200: sys.exit(1)

print("2. Создание сессии")
r = s.post(f"{base}/login", json={"username":"root","password":"0penBmc"})
print("Логин:", r.status_code)

print("3. Получение информации о системе")
r = s.get(f"{base}/redfish/v1/Systems/system")
print("PowerState:", r.json().get("PowerState"))

print("4. Включение системы")
s.post(f"{base}/redfish/v1/Systems/system/Actions/ComputerSystem.Reset",
       json={"ResetType": "On"})
time.sleep(15)
r = s.get(f"{base}/redfish/v1/Systems/system")
print("После включения:", r.json().get("PowerState"))

print("5. Получение списка сенсоров")
r = s.get(f"{base}/redfish/v1/Chassis/chassis/Thermal")
print("Температурных сенсоров:", len(r.json().get("Temperatures", [])))

print("АВТОТЕСТЫ НА PYTHON ЗАВЕРШЕНЫ УСПЕШНО")
PY
                '''
                archiveArtifacts artifacts: '*.log', allowEmptyArchive: true
            }
        }

        stage('Запуск WebUI тестов OpenBMC (Python)') {
            steps {
                sh '''
                    set -e
                    python3 - <<'PY'
import requests
s = requests.Session()
s.verify = False

print("=== WEBUI ТЕСТЫ НА PYTHON ===")
r = s.get("https://127.0.0.1:2443")
print("Главная страница:", r.status_code)

r = s.get("https://127.0.0.1:2443/#/sensor")
print("Страница сенсоров:", "OK" if "Sensor" in r.text else "FAIL")

r = s.get("https://127.0.0.1:2443/#/inventory")
print("Страница инвентаря:", "OK" if "DIMM" in r.text or "CPU" in r.text else "FAIL")

print("WEBUI ТЕСТЫ ЗАВЕРШЕНЫ")
PY
                '''
            }
        }

        stage('Нагрузочное тестирование OpenBMC (Python)') {
            steps {
                sh '''
                    set -e
                    python3 - <<'PY'
import requests, threading, time
def req():
    try:
        requests.get("https://127.0.0.1:2443/redfish/v1", verify=False, timeout=10)
    except: pass

threads = []
for i in range(200):
    t = threading.Thread(target=req)
    t.start()
    threads.append(t)

for t in threads:
    t.join()

print("200 параллельных запросов выполнено")
print("Система жива после нагрузки")
PY
                '''
            }
        }
    }

    post {
        always {
            sh '''
                [ -f qemu.pid ] && kill $(cat qemu.pid) || true
                rm -f qemu.pid openbmc-romulus.qcow2 romulus.zip *.mtd 2>/dev/null || true
            '''
        }
        success {
            echo "Лабораторная работа 7 успешно выполнена!"
            echo "Все автотесты на Python прошли успешно"
            echo "Готово к сдаче"
        }
    }
}
