pipeline {
    agent any

    stages {
        stage('Build') {
            steps {
                sh '''
                    /opt/anaconda3/bin/python3 -m venv .venv
                    . .venv/bin/activate
                    python -m pip install --upgrade pip
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