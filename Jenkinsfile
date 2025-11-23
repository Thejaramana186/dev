pipeline {
    agent {
        kubernetes {
            yaml '''
apiVersion: v1
kind: Pod
spec:
  containers:
  - name: tools
    image: docker:24.0.5-cli
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
'''
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

        stage('Install AWS CLI') {
            steps {
                container('tools') {
                    sh '''
                        echo "=== Installing AWS CLI ==="
                        apk add --no-cache python3 py3-pip curl
                        pip3 install awscli
                        aws --version
                    '''
                }
            }
        }

        stage('Build & Push to ECR') {
            steps {
                container('tools') {
                    sh '''
                        echo "=== Logging into AWS ECR ==="
                        aws ecr describe-repositories --repository-names stock-app --region $AWS_REGION || \
                        aws ecr create-repository --repository-name stock-app --region $AWS_REGION

                        aws ecr get-login-password --region $AWS_REGION | \
                        docker login --username AWS --password-stdin $ECR_REPO

                        echo "=== Building Docker image ==="
                        docker build -t $ECR_REPO:$IMAGE_TAG -t $ECR_REPO:latest .

                        echo "=== Pushing Docker image ==="
                        docker push $ECR_REPO:$IMAGE_TAG
                        docker push $ECR_REPO:latest
                    '''
                }
            }
        }
    }

    post {
        success {
            echo "✅ Successfully built and pushed to ECR!"
        }
        failure {
            echo "❌ Build failed. Check logs."
        }
    }
}
