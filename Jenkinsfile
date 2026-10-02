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
                    echo "Building Docker image"

                    docker --version

                    docker build \
                        -t sydney-house-price:${BUILD_NUMBER} \
                        .
                '''
            }
        }

        stage('Test') {
            steps {
                sh '''
                    echo "Running automated tests"

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
                            echo "Running SonarQube code quality analysis"

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
                    echo "Running security scans"

                    . .venv/bin/activate

                    echo "Running Bandit source-code scan"

                    bandit -r app.py

                    echo "Running Trivy Docker image scan"

                    trivy image \
                        --severity HIGH,CRITICAL \
                        sydney-house-price:${BUILD_NUMBER}
                '''
            }
        }

        stage('Deploy') {
            steps {
                sh '''
                    echo "Deploying application to staging environment"

                    docker rm -f sydney-house-price-staging || true

                    docker run -d \
                        --name sydney-house-price-staging \
                        -p 8502:8501 \
                        sydney-house-price:${BUILD_NUMBER}

                    echo "Waiting for staging application to start"

                    for i in {1..12}
                    do
                        if curl -f http://localhost:8502/_stcore/health
                        then
                            echo "Staging application is healthy"
                            exit 0
                        fi

                        echo "Waiting for application..."
                        sleep 5
                    done

                    echo "Staging deployment failed health check"

                    docker logs sydney-house-price-staging

                    exit 1
                '''
            }
        }
    }
}