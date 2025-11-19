pipeline {
    agent {
        kubernetes {
            inheritFrom 'jenkins-jenkins-agent'
            defaultContainer 'tools'
        }
    }

    environment {
        AWS_REGION = "us-east-1"
        ECR_ACCOUNT = "979750876373"
        ECR_REPO = "${ECR_ACCOUNT}.dkr.ecr.${AWS_REGION}.amazonaws.com/stock-app"
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

        stage('Docker Build & Push') {
            steps {
                container('docker') {
                    sh '''
                        echo "=== Installing AWS CLI ==="
                        apk add --no-cache python3 py3-pip
                        pip3 install awscli

                        echo "=== Logging into ECR ==="
                        aws ecr get-login-password --region $AWS_REGION \
                            | docker login --username AWS --password-stdin $ECR_ACCOUNT.dkr.ecr.$AWS_REGION.amazonaws.com

                        echo "=== Building Docker image ==="
                        docker build -t $ECR_REPO:$IMAGE_TAG .

                        echo "=== Pushing Docker image to ECR ==="
                        docker push $ECR_REPO:$IMAGE_TAG
                    '''
                }
            }
        }

    }
}
