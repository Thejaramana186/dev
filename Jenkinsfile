pipeline {
    agent any

    tools {
        dockerTool 'docker'
    }

    environment {
        AWS_REGION = "us-east-1"
        ECR_ACCOUNT = "979750876373"
        ECR_REPO = "${ECR_ACCOUNT}.dkr.ecr.${AWS_REGION}.amazonaws.com/stock-app"
        IMAGE_TAG = "v${BUILD_NUMBER}"
    }

    stages {
        stage('Checkout Code') {
            steps {
                echo "=== Checking out repository ==="
                checkout scm
            }
        }

        stage('Login to AWS ECR') {
            steps {
                echo "=== Logging into AWS ECR ==="
                sh '''
                    aws ecr describe-repositories --repository-names stock-app --region $AWS_REGION || \
                    aws ecr create-repository --repository-name stock-app --region $AWS_REGION

                    aws ecr get-login-password --region $AWS_REGION | docker login --username AWS --password-stdin $ECR_ACCOUNT.dkr.ecr.$AWS_REGION.amazonaws.com
                '''
            }
        }

        stage('Build Docker Image') {
            steps {
                echo "=== Building Docker image ==="
                sh '''
                    docker build -t $ECR_REPO:$IMAGE_TAG -t $ECR_REPO:latest .
                '''
            }
        }

        stage('Push Docker Image to ECR') {
            steps {
                echo "=== Pushing Docker image to ECR ==="
                sh '''
                    docker push $ECR_REPO:$IMAGE_TAG
                    docker push $ECR_REPO:latest
                '''
            }
        }
    }

    post {
        success {
            echo "✅ Docker image built and pushed to ECR successfully!"
        }
        failure {
            echo "❌ Build failed. Check the logs for details."
        }
    }
}
