pipeline {
    agent any

    environment {
        AWS_REGION = "us-east-1"
        ECR_ACCOUNT = "979750876373"
        ECR_REPO = "${ECR_ACCOUNT}.dkr.ecr.${AWS_REGION}.amazonaws.com/stock-app"
        IMAGE_TAG = "v${BUILD_NUMBER}"
    }

    stages {
        stage('Install AWS CLI and Docker (if missing)') {
            steps {
                sh '''
                    echo "=== Installing AWS CLI and Docker ==="
                    if ! command -v aws >/dev/null 2>&1; then
                        apt-get update -y || yum update -y
                        apt-get install -y python3-pip docker.io || yum install -y python3-pip docker
                        pip3 install awscli
                    fi
                    docker --version || echo "Docker installed successfully"
                '''
            }
        }

        stage('Checkout Code') {
            steps {
                echo "=== Checking out code from GitHub ==="
                checkout scm
            }
        }

        stage('Login to AWS ECR') {
            steps {
                sh '''
                    echo "=== Logging into AWS ECR ==="
                    aws ecr describe-repositories --repository-names stock-app --region $AWS_REGION || \
                    aws ecr create-repository --repository-name stock-app --region $AWS_REGION
                    
                    aws ecr get-login-password --region $AWS_REGION | \
                    docker login --username AWS --password-stdin $ECR_REPO
                '''
            }
        }

        stage('Build Docker Image') {
            steps {
                sh '''
                    echo "=== Building Docker Image ==="
                    docker build -t $ECR_REPO:$IMAGE_TAG -t $ECR_REPO:latest .
                '''
            }
        }

        stage('Push Docker Image to ECR') {
            steps {
                sh '''
                    echo "=== Pushing Docker Image to ECR ==="
                    docker push $ECR_REPO:$IMAGE_TAG
                    docker push $ECR_REPO:latest
                '''
            }
        }

        stage('Clean Up Docker') {
            steps {
                sh '''
                    echo "=== Cleaning up Docker images ==="
                    docker system prune -af || true
                '''
            }
        }
    }

    post {
        success {
            echo "✅ Successfully pushed image to ECR!"
        }
        failure {
            echo "❌ Build failed. Check logs."
        }
    }
}
