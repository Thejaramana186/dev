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
  - name: docker
    image: docker:24.0.5-dind
    securityContext:
      privileged: true
    command:
      - dockerd-entrypoint.sh
    args:
      - "--host=tcp://0.0.0.0:2375"
    ports:
      - containerPort: 2375
    volumeMounts:
      - name: docker-storage
        mountPath: /var/lib/docker
  - name: tools
    image: docker:24.0.5-cli
    tty: true
    env:
      - name: DOCKER_HOST
        value: tcp://localhost:2375
    command:
      - sh
      - -c
      - cat
    volumeMounts:
      - name: docker-storage
        mountPath: /var/lib/docker
  volumes:
  - name: docker-storage
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
                container('tools') {
                    sh '''
                      apk add --no-cache git -y 
                      git clone -b ${GIT_BRANCH} https://github.com/Thejaramana186/dev.git .
                    '''
                }
            }
        }

        stage('Build & Push Docker Image') {
            steps {
                container('tools') {
                    sh '''
                      echo "=== Installing AWS CLI ==="
                      apk add --no-cache python3 py3-pip
                      pip3 install awscli

                      echo "=== Logging into ECR ==="
                      aws ecr get-login-password --region $AWS_REGION \
                        | docker login --username AWS --password-stdin $ECR_REPO

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
