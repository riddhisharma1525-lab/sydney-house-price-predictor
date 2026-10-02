pipeline {
    agent any

    stages {
        stage('Build') {
            steps {
                sh '''
                    python3 -m venv .venv
                    . .venv/bin/activate
                    pip install -r requirements.txt
                '''
            }
        }

        stage('Test') {
            steps {
                echo 'Testing application'
            }
        }
    }
}