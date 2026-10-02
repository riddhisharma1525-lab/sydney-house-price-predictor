pipeline {
    agent any

    stages {
        stage('Build') {
            steps {
                sh '''
                    docker build -t sydney-house-price:${BUILD_NUMBER} .
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