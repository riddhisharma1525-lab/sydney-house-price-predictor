pipeline {
    agent any

    environment {
        PATH = "/Applications/Docker.app/Contents/Resources/bin:/usr/local/bin:/opt/homebrew/bin:/usr/bin:/bin:/usr/sbin:/sbin"
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

                    pytest -v
                '''
            }
        }
    }
}