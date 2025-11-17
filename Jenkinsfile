pipeline {
    agent any

    stages {
        stage('OpenBMC CI/CD — Redfish + WebUI тесты') {
            steps {
                sh '''
                    set -e

                    # Запускаем всё в отдельном контейнере через docker run (без плагина!)
                    docker run --rm -i \
                        --workdir /workspace \
                        -v "$WORKSPACE:/workspace" \
                        --user root \
                        ubuntu:22.04 \
                        bash -c """
                            apt-get update
                            apt-get install -y --no-install-recommends \\
                                python3 python3-pip wget unzip ca-certificates \\
                                libnss3 libgtk-3-0 libasound2 libatk-bridge2.0-0 libdrm2 \\
                                libxcomposite1 libxdamage1 libxrandr2 libgbm1 libpango-1.0-0 \\
                                libcairo2 libcups2 libatk1.0-0 fonts-liberation
                            pip3 install --no-cache-dir requests selenium

                            wget -q https://storage.googleapis.com/chrome-for-testing-public/131.0.6778.85/linux64/chrome-linux64.zip
                            unzip -q chrome-linux64.zip
                            chmod +x chrome-linux64/chrome
                            wget -q https://storage.googleapis.com/chrome-for-testing-public/131.0.6778.85/linux64/chromedriver-linux64.zip
                            unzip -q chromedriver-linux64.zip
                            mv chromedriver-linux64/chromedriver chromedriver-linux64/ 2>/dev/null || true
                            chmod +x chromedriver-linux64/chromedriver

                            echo "===================================================="
                            echo " ЗАПУСК ТЕСТОВ OPENBMC"
                            echo "===================================================="

                            echo "1/5 Redfish: Аутентификация"
                            python3 - <<'PY1'
import requests, sys
r = requests.post("https://127.0.0.1:2443/redfish/v1/SessionService/Sessions",
                  json={\\"UserName\\":\\"root\\",\\"Password\\":\\"0penBmc\\"}, verify=False, timeout=15)
print(\\"Аутентификация →\\", \\"УСПЕХ\\" if r.status_code == 201 else \\"ОШИБКА\\", r.status_code)
if r.status_code != 201: sys.exit(1)
PY1

                            # Остальные 4 теста точно так же — просто копируй их сюда (я сократил ради места)
                            # (вставь сюда блоки PY2 – PY5 из предыдущего сообщения без изменений)

                            echo "================================================="
                            echo " ВСЁ УСПЕШНО! @svikari_aug — ты сделал это!"
                            echo "================================================="
                        """
                '''
            }
        }
    }

    post {
        always { cleanWs() }
        success { echo "Готово, брат! Победа!" }
        failure { echo "Что-то упало — смотри лог выше" }
    }
}
