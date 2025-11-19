pipeline {
    agent {
        kubernetes {
            inheritFrom 'jenkins-jenkins-agent'
            defaultContainer 'tools'
        }
    }

    environment {
        AWS_REGION = "us-east-1"
        ECR_REPO = "979750876373.dkr.ecr.us-east-1.amazonaws.com/stock-app"
        IMAGE_TAG = "v${BUILD_NUMBER}"
        GIT_BRANCH = "main"
    }

    stages {

        stage('Checkout Code') {
            steps {
                checkout([$class: 'GitSCM',
                    branches: [[name: "*/${GIT_BRANCH}"]],
                    userRemoteConfigs: [[
                        url: 'https://github.com/Thejaramana186/dev.git',
                        credentialsId: 'github-creds'
                    ]]
                ])
            }
        }

        stage('Docker Build') {
            steps {
                container('docker') {
                    sh '''
                        echo "Logging into ECR..."
                        aws ecr get-login-password --region $AWS_REGION \
                          | docker login --username AWS --password-stdin ${ECR_REPO%/*}

                        echo "Building Docker image..."
                        docker build -t $ECR_REPO:$IMAGE_TAG .
                    '''
                }
            }
        }

        stage('Docker Push') {
            steps {
                container('docker') {
                    sh '''
                        echo "Pushing to ECR..."
                        docker push $ECR_REPO:$IMAGE_TAG
                    '''
                }
            }
        }

    }
}
