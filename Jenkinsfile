pipeline {
    agent {
        kubernetes {
            yaml '''
apiVersion: v1
kind: Pod
spec:
  serviceAccountName: jenkins
  containers:
  - name: kaniko
    image: gcr.io/kaniko-project/executor:debug   # ✅ use debug version for shell
    command:
    - /busybox/sh
    args:
    - -c
    - cat
    tty: true
    envFrom:
    - secretRef:
        name: aws-credentials
    volumeMounts:
    - name: workspace-volume
      mountPath: /home/jenkins/agent

  - name: aws
    image: amazon/aws-cli:2.15.13
    command:
    - cat
    tty: true
    envFrom:
    - secretRef:
        name: aws-credentials

  volumes:
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

        stage('Login to AWS ECR') {
            steps {
                container('aws') {
                    sh '''
                        echo "=== Ensuring ECR Repository Exists ==="
                        aws ecr describe-repositories --repository-names stock-app --region $AWS_REGION || \
                        aws ecr create-repository --repository-name stock-app --region $AWS_REGION

                        echo "=== Verifying AWS Authentication ==="
                        aws sts get-caller-identity
                    '''
                }
            }
        }

        stage('Build & Push Docker Image (Kaniko)') {
            steps {
                container('kaniko') {
                    sh '''
                        echo "=== Building and pushing image to ECR with Kaniko ==="

                        mkdir -p /kaniko/.docker
                        cat <<EOF > /kaniko/.docker/config.json
                        {
                          "credHelpers": {
                            "${AWS_REGION}": "ecr-login"
                          }
                        }
EOF

                        /kaniko/executor \
                          --context `pwd` \
                          --dockerfile `pwd`/Dockerfile \
                          --destination $ECR_REPO:$IMAGE_TAG \
                          --destination $ECR_REPO:latest \
                          --verbosity info
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
