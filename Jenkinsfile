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
  - name: tools
    image: gcr.io/kaniko-project/executor:latest
    tty: true
    command:
      - sh
    args:
      - -c
      - cat
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
                container('tools') {
                    checkout([$class: 'GitSCM',
                        branches: [[name: "*/${GIT_BRANCH}"]],
                        userRemoteConfigs: [[
                            url: 'https://github.com/Thejaramana186/dev.git',
                            credentialsId: 'github-creds'
                        ]]
                    ])
                }
            }
        }

        stage('Build & Push to ECR') {
            steps {
                container('tools') {
                    sh '''
                        echo "=== Installing AWS CLI ==="
                        apk add --no-cache python3 py3-pip >/dev/null
                        pip3 install awscli >/dev/null

                        echo "=== Building & Pushing Docker Image via Kaniko ==="
                        mkdir -p /kaniko/.docker
                        echo "{\"credHelpers\": {\"${AWS_REGION}.amazonaws.com\": \"ecr-login\"}}" > /kaniko/.docker/config.json

                        /kaniko/executor \
                          --context . \
                          --dockerfile Dockerfile \
                          --destination $ECR_REPO:$IMAGE_TAG \
                          --cache=true \
                          --cache-dir=/cache
                    '''
                }
            }
        }
    }
}
