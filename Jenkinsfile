pipeline {
    agent {
        kubernetes {
            yaml """
apiVersion: v1
kind: Pod
metadata:
  labels:
    jenkins: agent
spec:
  serviceAccountName: jenkins
  containers:
  - name: alpine
    image: alpine:3.18
    command:
      - cat
    tty: true
    volumeMounts:
      - name: jenkins-workspace
        mountPath: /home/jenkins/agent
  - name: kaniko
    image: gcr.io/kaniko-project/executor:latest
    command:
      - /kaniko/executor
    args:
      - "--context=/home/jenkins/agent"
      - "--dockerfile=/home/jenkins/agent/Dockerfile"
      - "--destination=979750876373.dkr.ecr.us-east-1.amazonaws.com/stock-app:v$BUILD_NUMBER"
      - "--cache=true"
      - "--cache-dir=/cache"
    volumeMounts:
      - name: jenkins-workspace
        mountPath: /home/jenkins/agent
      - name: kaniko-cache
        mountPath: /cache
  volumes:
  - name: jenkins-workspace
    persistentVolumeClaim:
      claimName: jenkins
  - name: kaniko-cache
    emptyDir: {}
"""
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
                container('alpine') {
                    sh '''
                      apk add --no-cache git
                      git clone -b ${GIT_BRANCH} https://github.com/Thejaramana186/dev.git .
                    '''
                }
            }
        }

        stage('Build & Push to ECR') {
            steps {
                container('alpine') {
                    sh '''
                      echo "=== Installing AWS CLI ==="
                      apk add --no-cache python3 py3-pip
                      pip3 install awscli

                      echo "=== Creating Docker config for Kaniko ==="
                      mkdir -p /kaniko/.docker
                      echo "{\"credHelpers\": {\"${AWS_REGION}.amazonaws.com\": \"ecr-login\"}}" > /kaniko/.docker/config.json
                    '''
                }
                container('kaniko') {
                    echo "🚀 Building and pushing Docker image using Kaniko..."
                }
            }
        }
    }
}
