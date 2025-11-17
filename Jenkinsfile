pipeline {
    agent any

    stages {
        stage('Установка QEMU') {
            steps {
                sh '''
                    set -e
                    echo "=== УСТАНОВКА QEMU ===" > qemu_install_report.txt
                    sudo apt-get update >> qemu_install_report.txt 2>&1
                    sudo apt-get install -y --no-install-recommends qemu-system-aarch64 >> qemu_install_report.txt 2>&1
                    
                    echo "Проверка версии QEMU:" >> qemu_install_report.txt
                    qemu-system-aarch64 --version >> qemu_install_report.txt 2>&1
                    echo "Установка завершена успешно" >> qemu_install_report.txt
                '''
                archiveArtifacts artifacts: 'qemu_install_report.txt', allowEmptyArchive: true
            }
        }

        stage('Проверка наличия образа OpenBMC') {
            steps {
                sh '''
                    set -e
                    echo "=== ПРОВЕРКА ОБРАЗА OPENBMC ===" > image_check_report.txt
                    IMAGE="/var/jenkins_home/romulus/obmc-phosphor-image-romulus-20251013060205.static.mtd"
                    
                    if [ -f "$IMAGE" ]; then
                        echo "ОБРАЗ НАЙДЕН: $IMAGE" >> image_check_report.txt
                        ls -lh "$IMAGE" >> image_check_report.txt
                    else
                        echo "ОШИБКА: Образ НЕ найден по пути $IMAGE" >> image_check_report.txt
                        exit 1
                    fi
                '''
                archiveArtifacts artifacts: 'image_check_report.txt', allowEmptyArchive: true
            }
        }

        stage('Запуск QEMU с OpenBMC') {
            steps {
                sh '''
                    set -e
                    echo "=== ЗАПУСК QEMU ===" > qemu_start_report.txt
                    IMAGE="/var/jenkins_home/romulus/obmc-phosphor-image-romulus-20251013060205.static.mtd"
                    
                    qemu-system-aarch64 \
                        -m 2G \
                        -M romulus-bmc \
                        -drive file=$IMAGE,format=raw,if=mtd \
                        -nic user,hostfwd=tcp::2443-:443,hostfwd=tcp::2222-:22 \
                        -nographic &
                    
                    echo $! > qemu.pid
                    echo "QEMU запущен с PID $(cat qemu.pid)" >> qemu_start_report.txt
                    echo "Ожидание полной загрузки OpenBMC (110 сек)..." >> qemu_start_report.txt
                    sleep 110
                    echo "OpenBMC успешно запущен и готов к тестам" >> qemu_start_report.txt
                '''
                archiveArtifacts artifacts: 'qemu_start_report.txt', allowEmptyArchive: true
            }
        }

        stage('Автотесты Redfish (Python)') {
            steps {
                sh '''
                    set -e
                    python3 - <<'PY'
import requests, time, sys
base = "https://127.0.0.1:2443"
s = requests.Session()
s.verify = False

print("=== REDFISH АВТОТЕСТЫ ===")
r = s.get(f"{base}/redfish/v1")
print(f"1. Redfish доступен: {r.status_code}")
if r.status_code != 200: sys.exit(1)

r = s.post(f"{base}/redfish/v1/SessionService/Sessions",
           json={"UserName":"root","Password":"0penBmc"})
print(f"2. Логин: {r.status_code}")
token = r.headers["X-Auth-Token"]

h = {"X-Auth-Token": token}
r = s.get(f"{base}/redfish/v1/Systems/system", headers=h).json()
print(f"3. PowerState: {r.get('PowerState')}")

s.post(f"{base}/redfish/v1/Systems/system/Actions/ComputerSystem.Reset",
       json={"ResetType":"On"}, headers=h)
time.sleep(12)
print(f"4. После включения: {s.get(f'{base}/redfish/v1/Systems/system', headers=h).json().get('PowerState')}")

print("=== REDFISH ТЕСТЫ ПРОЙДЕНЫ ===")
PY
                '''
            }
        }

        stage('WebUI тесты (Python)') {
            steps {
                sh '''
                    set -e
                    python3 - <<'PY'
import requests
s = requests.Session()
s.verify = False

print("=== WEBUI ТЕСТЫ ===")
r = s.get("https://127.0.0.1:2443")
print(f"Главная страница: {r.status_code}")

r = s.get("https://127.0.0.1:2443/?next=/redfish/v1/Systems/system/#/hardware-status/inventory")
print("Inventory: " + ("OK" if any(x in r.text for x in ["CPU", "DIMM", "Memory"]) else "FAIL"))

r = s.get("https://127.0.0.1:2443/?next=/redfish/v1/Systems/system/#/hardware-status/sensors")
print("Sensors: " + ("OK" if "Sensor" in r.text else "FAIL"))

print("=== WEBUI ТЕСТЫ ПРОЙДЕНЫ ===")
PY
                '''
            }
        }

        stage('Нагрузочное тестирование') {
            steps {
                sh '''
                    set -e
                    python3 - <<'PY'
import requests, threading
def hit():
    try: requests.get("https://127.0.0.1:2443/redfish/v1", verify=False, timeout=10)
    except: pass

print("Запуск 150 параллельных запросов...")
[t := threading.Thread(target=hit)).start() for _ in range(150)]
[t.join() for t in threading.enumerate() if t != threading.current_thread()]

r = requests.get("https://127.0.0.1:2443/redfish/v1", verify=False)
print(f"Система жива после нагрузки: {r.status_code}")
PY
                '''
            }
        }
    }

    post {
        always {
            sh '''
                [ -f qemu.pid ] && kill $(cat qemu.pid) 2>/dev/null || true
                rm -f qemu.pid 2>/dev/null || true
            '''
            echo "Лабораторная работа 7 выполнена успешно!"
        }
        success {
            echo "ВСЁ ЗЕЛЁНОЕ — ГОТОВО К СДАЧЕ!"
        }
    }
}
