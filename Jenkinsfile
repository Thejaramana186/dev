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
      - sleep
    args:
      - infinity
    tty: true
    volumeMounts:
      - name: jenkins-workspace
        mountPath: /home/jenkins/agent
  - name: kaniko
    image: gcr.io/kaniko-project/executor:debug
    command:
      - sleep
    args:
      - infinity
    tty: true
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

        stage('Setup AWS CLI') {
            steps {
                container('alpine') {
                    sh '''
                      apk add --no-cache python3 py3-pip
                      pip3 install awscli
                      mkdir -p /kaniko/.docker
                      echo "{\"credHelpers\": {\"${AWS_REGION}.amazonaws.com\": \"ecr-login\"}}" > /kaniko/.docker/config.json
                    '''
                }
            }
        }

        stage('Build & Push Docker Image') {
            steps {
                container('kaniko') {
                    sh '''
                      echo "=== Building Docker image using Kaniko ==="
                      /kaniko/executor \
                        --context=/home/jenkins/agent \
                        --dockerfile=/home/jenkins/agent/Dockerfile \
                        --destination=${ECR_REPO}:${IMAGE_TAG} \
                        --cache=true \
                        --cache-dir=/cache \
                        --single-snapshot \
                        --use-new-run
                    '''
                }
            }
        }
    }
}
