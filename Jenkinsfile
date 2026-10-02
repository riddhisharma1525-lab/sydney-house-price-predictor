pipeline {
    agent any

    environment {
        PATH = "/Applications/Docker.app/Contents/Resources/bin:/opt/homebrew/opt/openjdk@17/bin:/usr/local/bin:/opt/homebrew/bin:/usr/bin:/bin:/usr/sbin:/sbin"
        JAVA_HOME = "/opt/homebrew/opt/openjdk@17/libexec/openjdk.jdk/Contents/Home"
    }

    stages {
        stage('Build') {
            steps {
                sh '''
                    docker --version
                    docker build -t sydney-house-price:${BUILD_NUMBER} .
                '''
            }
        }

        stage('Test') {
            steps {
                sh '''
                    rm -rf .venv
                    /opt/anaconda3/bin/python3 -m venv .venv
                    . .venv/bin/activate

                    python -m pip install --upgrade pip
                    pip install -r requirements.txt

                    PYTHONPATH=. python -m pytest -v
                '''
            }
        }

        stage('Code Quality') {
            steps {
                script {
                    def scannerHome = tool 'SonarScanner'

                    withSonarQubeEnv('SonarQube') {
                        sh """
                            java -version

                            ${scannerHome}/bin/sonar-scanner \
                              -Dsonar.projectKey=sydney-house-price-predictor \
                              -Dsonar.sources=. \
                              -Dsonar.python.version=3.13 \
                              -Dsonar.exclusions=.venv/**,tests/**,screenshots/**,syd_house_price.ipynb
                        """
                    }
                }
            }
        }

        stage('Security') {
            steps {
                sh '''
                    . .venv/bin/activate

                    echo "Running Bandit source-code scan"
                    bandit -r app.py

                    echo "Running Trivy Docker image scan"
                    trivy image --severity HIGH,CRITICAL sydney-house-price:${BUILD_NUMBER}
                '''
            }
        }
    }
}