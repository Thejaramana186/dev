pipeline {
    agent {
        kubernetes {
            yaml """
apiVersion: v1
kind: Pod
spec:
  containers:
  - name: tools
    image: amazon/aws-cli:2.15.13
    command:
    - cat
    tty: true
    volumeMounts:
    - name: docker-sock
      mountPath: /var/run/docker.sock
  volumes:
  - name: docker-sock
    hostPath:
      path: /var/run/docker.sock
"""
        }
    }

    environment {
        AWS_REGION = "us-east-1"
        ECR_ACCOUNT = "979750876373"
        ECR_REPO = "${ECR_ACCOUNT}.dkr.ecr.${AWS_REGION}.amazonaws.com/stock-app"
        IMAGE_TAG = "v${BUILD_NUMBER}"
    }

    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }

        stage('Build & Push to ECR') {
            steps {
                container('tools') {
                    sh '''
                        echo "=== Logging into AWS ECR ==="
                        aws ecr describe-repositories --repository-names stock-app --region $AWS_REGION || \
                        aws ecr create-repository --repository-name stock-app --region $AWS_REGION

                        aws ecr get-login-password --region $AWS_REGION | docker login --username AWS --password-stdin $ECR_REPO

                        echo "=== Building & Pushing Docker image ==="
                        docker build -t $ECR_REPO:$IMAGE_TAG -t $ECR_REPO:latest .
                        docker push $ECR_REPO:$IMAGE_TAG
                        docker push $ECR_REPO:latest
                    '''
                }
            }
        }
    }

    post {
        success {
            echo "✅ Flask app successfully built and pushed to ECR!"
        }
        failure {
            echo "❌ Build failed. Check logs."
        }
    }
}
