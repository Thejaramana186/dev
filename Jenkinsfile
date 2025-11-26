pipeline {
    agent {
        kubernetes {
            yaml '''
apiVersion: v1
kind: Pod
spec:
  serviceAccountName: jenkins
  containers:
  - name: docker
    image: docker:24.0.7-cli
    command:
    - cat
    tty: true
    volumeMounts:
    - name: docker-sock
      mountPath: /var/run/docker.sock
    - name: workspace-volume
      mountPath: /home/jenkins/agent
  volumes:
  - name: docker-sock
    hostPath:
      path: /var/run/docker.sock
  - name: workspace-volume
    emptyDir: {}
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
        stage('Checkout Code') {
            steps {
                echo "=== Checking out repository ==="
                checkout scm
            }
        }

        stage('Install AWS CLI') {
            steps {
                container('docker') {
                    sh '''
                        echo "=== Installing AWS CLI on Alpine ==="
                        apk add --no-cache aws-cli
                        aws --version
                    '''
                }
            }
        }

        stage('Login to AWS ECR & Push Image') {
            steps {
                container('docker') {
                    sh '''
                        echo "=== Logging into AWS ECR ==="
                        aws ecr describe-repositories --repository-names stock-app --region $AWS_REGION || \
                        aws ecr create-repository --repository-name stock-app --region $AWS_REGION

                        aws ecr get-login-password --region $AWS_REGION | docker login --username AWS --password-stdin $ECR_ACCOUNT.dkr.ecr.$AWS_REGION.amazonaws.com

                        echo "=== Building and pushing image to ECR ==="
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
            echo "✅ Docker image built and pushed to ECR successfully!"
        }
        failure {
            echo "❌ Build failed. Check logs for details."
        }
    }
}
