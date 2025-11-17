pipeline {
    agent any

    stages {
        stage('Environment Check') {
            steps {
                sh '''
                    echo "=== CI/CD FOR OPENBMC ===" > build_report.txt
                    echo "Workspace: $WORKSPACE" >> build_report.txt
                    echo "Date: $(date)" >> build_report.txt
                    echo "Python scripts found:" >> build_report.txt
                    ls -la *.py >> build_report.txt 2>&1
                '''
                archiveArtifacts 'build_report.txt'
            }
        }

        stage('Redfish Tests') {
            steps {
                sh '''
                    echo "=== REDFISH TESTS ===" >> build_report.txt
                    python3 test_auth.py         >> build_report.txt 2>&1 && echo "Auth test PASSED" >> build_report.txt || echo "Auth test FAILED" >> build_report.txt
                    python3 test_system_info.py  >> build_report.txt 2>&1 && echo "System info PASSED" >> build_report.txt || echo "System info FAILED" >> build_report.txt
                    python3 test_power_on.py     >> build_report.txt 2>&1 && echo "Power on PASSED" >> build_report.txt || echo "Power on FAILED" >> build_report.txt
                    echo "REDFISH TESTS COMPLETED" >> build_report.txt
                '''
            }
        }

        stage('WebUI Tests') {
            steps {
                sh '''
                    echo "=== WEBUI SELENIUM TESTS ===" >> build_report.txt
                    python3 sensor_test.py    >> build_report.txt 2>&1 && echo "Sensors page PASSED" >> build_report.txt || echo "Sensors page FAILED" >> build_report.txt
                    python3 inventory_test.py >> build_report.txt 2>&1 && echo "Inventory page PASSED" >> build_report.txt || echo "Inventory page FAILED" >> build_report.txt
                    echo "WEBUI TESTS COMPLETED" >> build_report.txt
                '''
            }
        }

        stage('Load Testing') {
            steps {
                sh '''
                    echo "=== LOAD TESTING (40 requests) ===" >> build_report.txt
                    echo "Sending 40 requests to Redfish API..." >> build_report.txt
                    for i in {1..40}; do
                        curl -ks https://localhost:2443/redfish/v1 >/dev/null && echo -n "." || echo -n "F"
                    done >> build_report.txt
                    echo "" >> build_report.txt
                    echo "LOAD TEST COMPLETED" >> build_report.txt
                '''
            }
        }
    }

    post {
        success {
            echo "LABORATORY WORK 7 COMPLETED SUCCESSFULLY"
            archiveArtifacts 'build_report.txt'
        }
    }
}
