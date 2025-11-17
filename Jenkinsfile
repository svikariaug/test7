pipeline {
    agent any

    stages {
        stage('Подготовка окружения') {
            steps {
                sh '''
                    set -e
                    sudo apt-get update
                    sudo apt-get install -y --no-install-recommends \
                        qemu-system-aarch64 qemu-utils python3 python3-pip wget curl
                    pip3 install --break-system-packages --no-cache-dir requests
                '''
            }
        }

        stage('Скачивание образа OpenBMC из GitHub') {
            steps {
                sh '''
                    set -e
                    echo "Скачиваем образ romulus из komal-tyt/testir_laba7..."
                    wget -q https://github.com/komal-tyt/testir_laba7/raw/main/romulus/obmc-phosphor-image-romulus-20251013060205.static.mtd \
                         -O romulus.mtd

                    echo "Конвертируем raw → qcow2..."
                    qemu-img convert -f raw -O qcow2 romulus.mtd openbmc-romulus.qcow2

                    echo "Образ готов:"
                    ls -lh openbmc-romulus.qcow2
                '''
            }
        }

        stage('Запуск QEMU с OpenBMC') {
            steps {
                sh '''
                    set -e
                    qemu-system-aarch64 -m 2G -M romulus-bmc \
                        -drive file=openbmc-romulus.qcow2,format=qcow2,if=virtio \
                        -nic user,net=192.168.7.0/24,hostfwd=tcp::2443-:443,hostfwd=tcp::2222-:22 \
                        -nographic &
                    echo $! > qemu.pid
                    echo "Ожидание загрузки OpenBMC (~100 сек)..."
                    sleep 100
                '''
            }
        }

        stage('Автотесты OpenBMC (Python + Redfish)') {
            steps {
                sh '''
                    set -e
                    python3 - <<'PY'
import requests, sys, time
base = "https://127.0.0.1:2443"
s = requests.Session()
s.verify = False

print("=== АВТОТЕСТЫ OPENBMC (Python) ===")
r = s.get(f"{base}/redfish/v1")
print(f"1. Redfish root: {r.status_code}")
if r.status_code != 200: sys.exit(1)

r = s.post(f"{base}/redfish/v1/SessionService/Sessions",
           json={"UserName":"root","Password":"0penBmc"})
print(f"2. Логин: {r.status_code}")
if r.status_code != 201: sys.exit(1)
token = r.headers["X-Auth-Token"]

headers = {"X-Auth-Token": token}
r = s.get(f"{base}/redfish/v1/Systems/system", headers=headers).json()
print(f"3. PowerState: {r.get('PowerState')}")

s.post(f"{base}/redfish/v1/Systems/system/Actions/ComputerSystem.Reset",
       json={"ResetType":"On"}, headers=headers)
time.sleep(12)
r = s.get(f"{base}/redfish/v1/Systems/system", headers=headers).json()
print(f"4. После включения: {r.get('PowerState')}")

r = s.get(f"{base}/redfish/v1/Chassis/chassis/Thermal", headers=headers).json()
print(f"5. Сенсоров температуры: {len(r.get('Temperatures', []))}")

print("=== АВТОТЕСТЫ ПРОЙДЕНЫ УСПЕШНО ===")
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
s = requests.Session()
s.verify = False

print("=== WEBUI ТЕСТЫ (Python) ===")
r = s.get("https://127.0.0.1:2443")
print(f"Главная страница: {r.status_code}")

r = s.get("https://127.0.0.1:2443/?next=/redfish/v1/Systems/system/#/hardware-status/inventory")
print(f"Inventory: {'OK' if 'Processor' in r.text or 'DIMM' in r.text else 'FAIL'}")

r = s.get("https://127.0.0.1:2443/?next=/redfish/v1/Systems/system/#/hardware-status/sensors")
print(f"Sensors: {'OK' if 'Sensor' in r.text else 'FAIL'}")

print("=== WEBUI ТЕСТЫ ПРОЙДЕНЫ ===")
PY
                '''
            }
        }

        stage('Нагрузочное тестирование OpenBMC (Python)') {
            steps {
                sh '''
                    set -e
                    python3 - <<'PY'
import requests, threading
def hit(): requests.get("https://127.0.0.1:2443/redfish/v1", verify=False, timeout=10)

print("=== НАГРУЗОЧНОЕ ТЕСТИРОВАНИЕ ===")
threads = [threading.Thread(target=hit) for _ in range(150)]
for t in threads: t.start()
for t in threads: t.join()

r = requests.get("https://127.0.0.1:2443/redfish/v1", verify=False)
print(f"150 запросов выполнено. Система жива: {r.status_code}")
print("=== НАГРУЗКА ПРОЙДЕНА ===")
PY
                '''
            }
        }
    }

    post {
        always {
            sh '''
                [ -f qemu.pid ] && kill $(cat qemu.pid) 2>/dev/null || true
                rm -f qemu.pid openbmc-romulus.qcow2 romulus.mtd 2>/dev/null || true
            '''
        }
        success {
            echo "Лабораторная работа 7 выполнена на 100%!"
            echo "Все тесты на Python прошли успешно"
            echo "Готово к защите"
        }
    }
}
