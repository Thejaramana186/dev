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
    image: gcr.io/kaniko-project/executor:latest
    args: ["--help"]
    tty: true
    volumeMounts:
    - name: kaniko-secret
      mountPath: /kaniko/.docker/
  volumes:
  - name: kaniko-secret
    secret:
      secretName: regcred
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
                checkout scm
            }
        }

        stage('Build & Push to ECR') {
            steps {
                container('kaniko') {
                    sh '''
                        echo "=== Building and pushing image using Kaniko ==="
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
            echo "✅ Image built and pushed to ECR successfully!"
        }
        failure {
            echo "❌ Build failed. Check logs."
        }
    }
}
