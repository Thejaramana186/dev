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
    image: gcr.io/kaniko-project/executor:debug
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

  - name: git
    image: alpine/git
    command:
    - cat
    tty: true

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

        # GitOps Repo Info
        GITOPS_REPO = "github.com/Theja-2709/Theja-gitops.git"
        GITOPS_FILE_PATH = "stack/deployment.yaml"
        GITOPS_BRANCH = "main"

        GIT_USERNAME = "Theja-2709"
        GIT_EMAIL = "theja@18.com"
    }

    stages {

        stage('Checkout App Code') {
            steps {
                echo "=== Checking out application repository ==="
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

        stage('Update GitOps Repository') {
            steps {
                container('git') {
                    withCredentials([usernamePassword(credentialsId: 'github-token', usernameVariable: 'GIT_USER', passwordVariable: 'GIT_TOKEN')]) {
                        sh '''
                            echo "=== Cloning GitOps repository ==="
                            git clone https://$GIT_USER:$GIT_TOKEN@$GITOPS_REPO gitops
                            cd gitops

                            echo "=== Updating image tag in deployment YAML ==="
                            sed -i "s|image: ${ECR_REPO}:.*|image: ${ECR_REPO}:${IMAGE_TAG}|g" $GITOPS_FILE_PATH

                            echo "=== Commit and push the updated image tag ==="
                            git config user.name "$GIT_USERNAME"
                            git config user.email "$GIT_EMAIL"
                            git add $GITOPS_FILE_PATH
                            git commit -m "Auto-update image tag to ${IMAGE_TAG}"
                            git push origin $GITOPS_BRANCH

                            echo "✅ GitOps repository updated successfully!"
                        '''
                    }
                }
            }
        }
    }

    post {
        success {
            echo "✅ Build successful — image pushed to ECR and GitOps repo updated."
        }
        failure {
            echo "❌ Build failed — check logs for details."
        }
    }
}
