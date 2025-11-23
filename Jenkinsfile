pipeline {
    agent {
        kubernetes {
            yaml '''
apiVersion: v1
kind: Pod
metadata:
  labels:
    jenkins: agent
spec:
  serviceAccountName: jenkins
  securityContext:
    runAsUser: 0
  shareProcessNamespace: true
  containers:
  - name: docker
    image: docker:24.0.5-dind
    securityContext:
      privileged: true
    command:
      - dockerd-entrypoint.sh
    args:
      - "--host=tcp://0.0.0.0:2375"
      - "--storage-driver=overlay2"
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
      - |
        echo "Waiting for Docker daemon to start..."
        for i in $(seq 1 20); do
          nc -z localhost 2375 && echo "Docker daemon ready!" && break
          echo "Retrying in 3s..."
          sleep 3
        done
        cat
    volumeMounts:
      - name: docker-storage
        mountPath: /var/lib/docker
  volumes:
  - name: docker-storage
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

        stage('Build & Push Docker Image') {
            steps {
                container('tools') {
                    sh '''
                      echo "=== Installing AWS CLI ==="
                      apk add --no-cache python3 py3-pip curl netcat-openbsd
                      pip3 install awscli

                      echo "=== Waiting for Docker daemon... ==="
                      for i in $(seq 1 10); do
                        docker version && break
                        echo "Docker not ready yet, retrying..."
                        sleep 3
                      done

                      echo "=== Login to ECR ==="
                      aws ecr get-login-password --region $AWS_REGION | docker login --username AWS --password-stdin $ECR_REPO

                      echo "=== Building and pushing image ==="
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
            echo "✅ Image pushed successfully to ECR!"
        }
        failure {
            echo "❌ Build failed. Check the logs."
        }
    }
}
