pipeline {
    agent any

    triggers {
        pollSCM('H/5 * * * *')
    }

    environment {
        PATH = "/Applications/Docker.app/Contents/Resources/bin:/opt/homebrew/opt/openjdk@17/bin:/usr/local/bin:/opt/homebrew/bin:/usr/bin:/bin:/usr/sbin:/sbin"
        JAVA_HOME = "/opt/homebrew/opt/openjdk@17/libexec/openjdk.jdk/Contents/Home"
        APP_VERSION = "1.0.${BUILD_NUMBER}"
    }

    stages {

        stage('Build') {
            steps {
                sh '''
                    echo "Building Docker image"
                    echo "Application version: ${APP_VERSION}"

                    docker --version

                    docker build \
                        -t sydney-house-price:${BUILD_NUMBER} \
                        -t sydney-house-price:${APP_VERSION} \
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

                    echo "Running unit tests"

                    PYTHONPATH=. python -m pytest -v

                    echo "Running integration test"

                    docker rm -f sydney-house-price-test || true

                    docker run -d \
                        --name sydney-house-price-test \
                        -p 8503:8501 \
                        sydney-house-price:${BUILD_NUMBER}

                    i=1

                    while [ "$i" -le 12 ]
                    do
                        if curl -fsS http://localhost:8503/_stcore/health
                        then
                            echo "Integration test passed"
                            break
                        fi

                        echo "Waiting for test application..."
                        sleep 5

                        i=$((i + 1))
                    done

                    if ! curl -fsS http://localhost:8503/_stcore/health > /dev/null
                    then
                        echo "Integration test failed"

                        docker logs sydney-house-price-test

                        docker rm -f sydney-house-price-test || true

                        exit 1
                    fi

                    docker rm -f sydney-house-price-test

                    echo "All tests passed"
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

                    echo "Waiting for SonarQube Quality Gate"

                    timeout(time: 2, unit: 'MINUTES') {
                        def qualityGate = waitForQualityGate()

                        if (qualityGate.status != 'OK') {
                            error "SonarQube Quality Gate failed: ${qualityGate.status}"
                        }

                        echo "SonarQube Quality Gate passed"
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

                    echo "Running Trivy critical vulnerability gate"

                    trivy image \
                        --scanners vuln \
                        --severity CRITICAL \
                        --ignore-unfixed \
                        --exit-code 1 \
                        sydney-house-price:${BUILD_NUMBER}

                    echo "Running full Trivy vulnerability report"

                    trivy image \
                        --scanners vuln \
                        --severity HIGH,CRITICAL \
                        sydney-house-price:${BUILD_NUMBER}

                    echo "Security checks completed"
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

                    i=1

                    while [ "$i" -le 12 ]
                    do
                        if curl -fsS http://localhost:8502/_stcore/health
                        then
                            echo "Staging application is healthy"
                            break
                        fi

                        echo "Waiting for staging application..."
                        sleep 5

                        i=$((i + 1))
                    done

                    if ! curl -fsS http://localhost:8502/_stcore/health > /dev/null
                    then
                        echo "Staging deployment failed health check"

                        docker logs sydney-house-price-staging

                        exit 1
                    fi
                '''
            }
        }

        stage('Release') {
            steps {
                sh '''
                    echo "Releasing application to production"

                    docker tag \
                        sydney-house-price:${BUILD_NUMBER} \
                        sydney-house-price:production

                    docker rm -f sydney-house-price-production || true

                    docker run -d \
                        --name sydney-house-price-production \
                        -p 8501:8501 \
                        sydney-house-price:production

                    echo "Waiting for production application to start"

                    i=1

                    while [ "$i" -le 12 ]
                    do
                        if curl -fsS http://localhost:8501/_stcore/health
                        then
                            echo "Production application is healthy"
                            break
                        fi

                        echo "Waiting for production application..."
                        sleep 5

                        i=$((i + 1))
                    done

                    if ! curl -fsS http://localhost:8501/_stcore/health > /dev/null
                    then
                        echo "Production release failed health check"

                        docker logs sydney-house-price-production

                        exit 1
                    fi
                '''
            }
        }

        stage('Monitoring') {
            steps {
                sh '''
                    echo "Starting monitoring and alerting services"

                    docker compose \
                        -f docker-compose.monitoring.yml \
                        up -d

                    echo "Checking monitoring services"

                    i=1

                    while [ "$i" -le 12 ]
                    do
                        if curl -fsS http://localhost:9090/-/ready > /dev/null && \
                           curl -fsS http://localhost:9093/-/ready > /dev/null && \
                           curl -fsS http://localhost:3000/api/health > /dev/null
                        then
                            echo "Monitoring services are running"
                            break
                        fi

                        echo "Waiting for monitoring services..."
                        sleep 5

                        i=$((i + 1))
                    done

                    if ! curl -fsS http://localhost:9090/-/ready > /dev/null
                    then
                        echo "Prometheus is not ready"
                        exit 1
                    fi

                    if ! curl -fsS http://localhost:9093/-/ready > /dev/null
                    then
                        echo "Alertmanager is not ready"
                        exit 1
                    fi

                    if ! curl -fsS http://localhost:3000/api/health > /dev/null
                    then
                        echo "Grafana is not ready"
                        exit 1
                    fi

                    echo "Checking production monitoring"

                    curl -fsS \
                        "http://localhost:9115/probe?target=http://host.docker.internal:8501/_stcore/health&module=http_2xx" \
                        | grep "probe_success 1"

                    echo "Production application is being monitored successfully"
                '''
            }
        }
    }
}