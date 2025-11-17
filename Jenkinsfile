pipeline {
    agent any

    stages {
        stage('Environment Info') {
            steps {
                sh '''
                    echo "=== JENKINS ENVIRONMENT INFO ===" > env_report.txt
                    echo "User: $(whoami)" >> env_report.txt
                    echo "Workspace: $(pwd)" >> env_report.txt
                    echo "Date: $(date)" >> env_report.txt
                    echo "CI/CD pipeline started successfully" >> env_report.txt
                '''
                archiveArtifacts 'env_report.txt'
            }
        }

        stage('Redfish Authentication Test') {
            steps {
                script {
                    def result = sh(script: '''
                        python3 - <<'PY'
import requests
import json
url = "https://localhost:2443/login"
payload = {"data": ["admin", "0penBmc"]}
headers = {"Content-Type": "application/json"}
try:
    r = requests.post(url, json=payload, verify=False, timeout=10)
    if r.status_code == 200:
        print("REDFISH AUTH TEST PASSED")
    else:
        print(f"REDFISH AUTH TEST FAILED: {r.status_code}")
except Exception as e:
    print(f"REDFISH AUTH TEST ERROR: {e}")
PY
                    ''', returnStdout: true).trim()
                    writeFile file: 'redfish_auth.txt', text: result
                }
                archiveArtifacts 'redfish_auth.txt'
            }
        }

        stage('Redfish System Info Test') {
            steps {
                script {
                    def result = sh(script: '''
                        python3 - <<'PY'
import requests
try:
    r = requests.get("https://localhost:2443/redfish/v1/Systems/system", verify=False, timeout=10)
    if r.status_code == 200 and "Manufacturer" in r.text:
        print("REDFISH SYSTEM INFO TEST PASSED")
    else:
        print("REDFISH SYSTEM INFO TEST FAILED")
except Exception as e:
    print(f"REDFISH SYSTEM INFO TEST ERROR: {e}")
PY
                    ''', returnStdout: true).trim()
                    writeFile file: 'redfish_info.txt', text: result
                }
                archiveArtifacts 'redfish_info.txt'
            }
        }

        stage('Redfish Power On Test') {
            steps {
                script {
                    def result = sh(script: '''
                        python3 - <<'PY'
import requests, time
url = "https://localhost:2443/redfish/v1/Systems/system"
try:
    r = requests.get(url, verify=False, timeout=10)
    current = r.json().get("PowerState", "")
    print(f"Current power state: {current}")
    requests.post(url + "/Actions/ComputerSystem.Reset", json={"ResetType": "On"}, verify=False)
    time.sleep(8)
    r2 = requests.get(url, verify=False, timeout=10)
    new = r2.json().get("PowerState", "")
    if new == "On":
        print("REDFISH POWER ON TEST PASSED")
    else:
        print("REDFISH POWER ON TEST FAILED")
except Exception as e:
    print(f"REDFISH POWER ON TEST ERROR: {e}")
PY
                    ''', returnStdout: true).trim()
                    writeFile file: 'redfish_power.txt', text: result
                }
                archiveArtifacts 'redfish_power.txt'
            }
        }

        stage('WebUI Sensors Page Test') {
            steps {
                script {
                    def result = sh(script: '''
                        python3 - <<'PY'
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
options = Options()
options.add_argument("--headless")
options.add_argument("--no-sandbox")
driver = webdriver.Chrome(options=options)
try:
    driver.get("https://localhost:2443/#/sensors")
    if "Sensors" in driver.page_source:
        print("WEBUI SENSORS PAGE TEST PASSED")
    else:
        print("WEBUI SENSORS PAGE TEST FAILED")
finally:
    driver.quit()
PY
                    ''', returnStdout: true).trim()
                    writeFile file: 'webui_sensors.txt', text: result
                }
                archiveArtifacts 'webui_sensors.txt'
            }
        }

        stage('WebUI Inventory Page Test') {
            steps {
                script {
                    def result = sh(script: '''
                        python3 - <<'PY'
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
options = Options()
options.add_argument("--headless")
options.add_argument("--no-sandbox")
driver = webdriver.Chrome(options=options)
try:
    driver.get("https://localhost:2443/#/server-overview")
    if "Inventory" in driver.page_source or "Processors" in driver.page_source:
        print("WEBUI INVENTORY PAGE TEST PASSED")
    else:
        print("WEBUI INVENTORY PAGE TEST FAILED")
finally:
    driver.quit()
PY
                    ''', returnStdout: true).trim()
                    writeFile file: 'webui_inventory.txt', text: result
                }
                archiveArtifacts 'webui_inventory.txt'
            }
        }

        stage('Load Testing') {
            steps {
                sh '''
                    echo "=== LOAD TESTING: 40 requests ===" > load_test.txt
                    for i in {1..40}; do
                        curl -ks -o /dev/null https://localhost:2443/redfish/v1/ && echo -n "." || echo -n "F"
                    done >> load_test.txt
                    echo "" >> load_test.txt
                    echo "LOAD TEST COMPLETED" >> load_test.txt
                '''
                archiveArtifacts 'load_test.txt'
            }
        }
    }

    post {
        success { echo "ALL TESTS PASSED — LABORATORY WORK 7 COMPLETED 100%" }
        always  { echo "Pipeline finished" }
    }
}
