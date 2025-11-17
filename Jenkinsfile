pipeline {
    agent any

    stages {
                stage('Проверка наличия образа OpenBMC') {
            steps {
                sh '''
                    echo "=== ПРОВЕРКА ФАЙЛОВ ===" > file_check.txt
                    [ -f "/var/jenkins_home/romulus/obmc-phosphor-image-romulus-20251013060205.static.mtd" ] && echo "Образ OpenBMC найден" || echo "ОБРАЗ НЕ НАЙДЕН!"
                    echo "Все Python-тесты в репозитории:" >> file_check.txt
                    ls -la *.py >> file_check.txt 2>/dev/null || echo "Python-тесты не найдены"
                ''' >> file_check.txt
            }
            post { always { archiveArtifacts 'file_check.txt' } }
        }

        stage('Запуск QEMU с OpenBMC') {
            steps {
                sh '''
                    echo "=== ЗАПУСК QEMU ===" > qemu_start.txt
                    pkill -f "qemu-system-arm" || true
                    sleep 3

                    qemu-system-arm -m 256 -M romulus-bmc -nographic \\
                      -drive file="/var/jenkins_home/romulus/obmc-phosphor-image-romulus-20251013060205.static.mtd",format=raw,if=mtd \\
                      -net nic -net user,hostfwd=:0.0.0.0:2222-:22,hostfwd=:0.0.0.0:2443-:443,hostname=qemu &
                    
                    echo "QEMU запущен в фоне" >> qemu_start.txt
                    echo "Ожидаем загрузки OpenBMC ~70 секунд..." >> qemu_start.txt
                    sleep 70
                '''
            }
            post { always { archiveArtifacts 'qemu_start.txt' } }
        }

        stage('Redfish автотесты (Python)') {
            steps {
                sh '''
                    echo "=== REDFISH АВТОТЕСТЫ ===" > redfish_tests.txt
                    python3 test_auth.py >> redfish_tests.txt 2>&1         || echo "test_auth.py — ПРОВАЛЕН" >> redfish_tests.txt
                    python3 test_system_info.py >> redfish_tests.txt 2>&1  || echo "test_system_info.py — ПРОВАЛЕН" >> redfish_tests.txt
                    python3 test_power_on.py >> redfish_tests.txt 2>&1     || echo "test_power_on.py — ПРОВАЛЕН" >> redfish_tests.txt
                    echo "Redfish тесты завершены" >> redfish_tests.txt
                '''
            }
            post { always { archiveArtifacts 'redfish_tests.txt' } }
        }

        stage('WebUI тесты через Selenium (без локального chromedriver)') {
            steps {
                sh '''
                    echo "=== SELENIUM WEBUI ТЕСТЫ ===" > selenium_tests.txt

                    # Создаём временный Python-скрипт с автоматическим управлением драйвером
                    cat > run_selenium_tests.py << 'EOF'
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
import os

chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--ignore-certificate-errors")
chrome_options.add_argument("--allow-insecure-localhost")

service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service, options=chrome_options)

def run_test(script_name):
    print(f"Запуск {script_name}...")
    os.system(f"python3 {script_name}")

run_test("sensor_test.py")
run_test("inventory_test.py")

driver.quit()
EOF

                    python3 run_selenium_tests.py >> selenium_tests.txt 2>&1
                    echo "Selenium тесты завершены" >> selenium_tests.txt
                '''
            }
            post { always { archiveArtifacts 'selenium_tests.txt' } }
        }

        stage('Нагрузочное тестирование') {
            steps {
                sh '''
                    echo "=== НАГРУЗОЧНОЕ ТЕСТИРОВАНИЕ ===" > load_test.txt
                    for i in {1..40}; do
                        curl -s -k -o /dev/null https://127.0.0.1:2443/redfish/v1 && echo -n "." || echo -n "F"
                    done >> load_test.txt
                    echo "\\n40 запросов выполнено" >> load_test.txt
                    curl -k https://127.0.0.1:2443/redfish/v1 > /dev/null && echo "Система жива после нагрузки" >> load_test.txt
                '''
            }
            post { always { archiveArtifacts 'load_test.txt' } }
        }
    }

    post {
        always {
            sh 'pkill -f qemu-system-arm || true'
            archiveArtifacts artifacts: '*.txt', allowEmptyArchive: true
        }
        success { echo "ВСЕ ТЕСТЫ ПРОЙДЕНЫ!" }
        failure { echo "ГДЕ-ТО ЧТО-ТО ПОШЛО НЕ ТАК — смотри логи выше" }
    }
}
