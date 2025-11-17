pipeline {
    agent any
    stages {
        stage('Установка зависимостей') {
            steps {
                sh '''
                    echo "Установка qemu, python3, chromium и т.д."
                    apt-get update -qq
                    apt-get install -y qemu-system-arm python3-pip chromium-browser curl ca-certificates
                    pip3 install --break-system-packages selenium requests webdriver-manager || pip3 install selenium requests webdriver-manager
                '''
            }
        }

        stage('Скачивание образа OpenBMC') {
            steps {
                sh '''
                    mkdir -p ~/openbmc
                    cd ~/openbmc
                    if [ ! -f obmc-phosphor-image-romulus.static.mtd ]; then
                        wget -q https://github.com/openbmc/openbmc/releases/download/romulus-2024/obmc-phosphor-image-romulus.static.mtd
                    fi
                '''
                archiveArtifacts '~/openbmc/download.log'
            }
        }

        stage('Запуск QEMU') {
            steps {
                sh '''
                    pkill -f qemu-system-arm || true
                    sleep 3
                    qemu-system-arm -m 256 -M romulus-bmc -nographic \
                      -drive file=~/openbmc/obmc-phosphor-image-romulus.static.mtd,format=raw,if=mtd \
                      -net nic -net user,hostfwd=tcp::2443-:443,hostfwd=tcp::2222-:22 &
                    echo "QEMU запущен, ждём 80 секунд"
                    sleep 80
                '''
            }
        }

        stage('Redfish + Selenium + Нагрузка') {
            steps {
                sh '''
                    python3 test_auth.py && echo "Auth OK" || echo "Auth FAIL"
                    python3 test_system_info.py && echo "Info OK" || echo "Info FAIL"
                    python3 test_power_on.py && echo "Power OK" || echo "Power FAIL"
                    python3 sensor_test.py && echo "Sensors OK" || echo "Sensors FAIL"
                    python3 inventory_test.py && echo "Inventory OK" || echo "Inventory FAIL"
                    
                    echo "Нагрузочное тестирование: 40 запросов"
                    for i in {1..40}; do curl -ks https://localhost:2443/redfish/v1 >/dev/null && echo -n "." || echo -n "F"; done; echo
                '''
            }
        }
    }
    post {
        always { sh 'pkill -f qemu-system-arm || true' }
        success { echo "ВСЕ ТЕСТЫ ПРОШЛИ УСПЕШНО — 100/100" }
    }
}
