pipeline {
    agent any

    stages {
        stage('Build') {
            steps {
                sh '''
                    /Applications/Docker.app/Contents/Resources/bin/docker --version
                    /Applications/Docker.app/Contents/Resources/bin/docker build -t sydney-house-price:${BUILD_NUMBER} .
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