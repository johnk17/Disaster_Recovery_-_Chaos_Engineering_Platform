import os

def write_file(path, content):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w') as f:
        f.write(content.strip() + '\n')

dockerfile = """
# Stage 1: Build
FROM maven:3.9-eclipse-temurin-21 AS builder
WORKDIR /app
COPY pom.xml .
COPY src ./src
RUN mvn package -DskipTests

# Stage 2: Runtime
FROM eclipse-temurin:21-jre-alpine
WORKDIR /app
RUN addgroup -S spring && adduser -S spring -G spring
USER spring:spring

COPY --from=builder /app/target/*.jar app.jar

ENV JAVA_OPTS="-XX:+UseContainerSupport -XX:MaxRAMPercentage=75.0"
EXPOSE 8080

ENTRYPOINT ["sh", "-c", "java $JAVA_OPTS -jar app.jar"]
"""

jenkinsfile = """
pipeline {
    agent { label 'linux' }
    environment {
        AWS_DEFAULT_REGION = 'us-east-1'
        ECR_REPO = 'my-service'
        IMAGE_TAG = "${env.BUILD_NUMBER}"
    }
    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }
        stage('Test') {
            steps {
                sh 'mvn test'
            }
            post {
                always {
                    junit 'target/surefire-reports/*.xml'
                }
            }
        }
        stage('Build') {
            steps {
                sh 'mvn package -DskipTests'
            }
        }
        stage('Docker Build & Push') {
            steps {
                withCredentials([aws(credentialsId: 'AWS_ACCESS_KEY', accessKeyVariable: 'AWS_ACCESS_KEY_ID', secretKeyVariable: 'AWS_SECRET_ACCESS_KEY')]) {
                    sh '''
                        aws ecr get-login-password --region $AWS_DEFAULT_REGION | docker login --username AWS --password-stdin $AWS_ACCOUNT_ID.dkr.ecr.$AWS_DEFAULT_REGION.amazonaws.com
                        docker build -t $ECR_REPO:$IMAGE_TAG -t $ECR_REPO:latest .
                        docker push $ECR_REPO:$IMAGE_TAG
                        docker push $ECR_REPO:latest
                    '''
                }
            }
        }
        stage('Security Scan') {
            steps {
                sh 'trivy image --exit-code 1 --severity CRITICAL $ECR_REPO:$IMAGE_TAG'
            }
        }
        stage('Deploy to EKS') {
            steps {
                sh 'kubectl set image deployment/my-service my-service=$ECR_REPO:$IMAGE_TAG -n production'
                sh 'kubectl rollout status deployment/my-service -n production'
            }
        }
        stage('Smoke Test') {
            steps {
                sh '''
                    STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://my-service.production.svc.cluster.local:8080/actuator/health)
                    if [ "$STATUS" -ne 200 ]; then
                        exit 1
                    fi
                '''
            }
        }
    }
    post {
        success {
            slackSend color: 'good', message: "SUCCESS: Job '${env.JOB_NAME} [${env.BUILD_NUMBER}]' (${env.BUILD_URL})"
        }
        failure {
            slackSend color: 'danger', message: "FAILED: Job '${env.JOB_NAME} [${env.BUILD_NUMBER}]' (${env.BUILD_URL})"
            script {
                if (env.PREVIOUS_IMAGE_TAG) {
                    sh "kubectl set image deployment/my-service my-service=$ECR_REPO:$PREVIOUS_IMAGE_TAG -n production"
                }
            }
        }
    }
}
"""

github_lint = """
name: Lint

on:
  pull_request:
    branches: [ "main", "develop" ]

jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    - name: Set up JDK 21
      uses: actions/setup-java@v3
      with:
        java-version: '21'
        distribution: 'temurin'
    - name: Run Checkstyle
      run: mvn checkstyle:check
"""

git_strategy = """
# Git Branching Strategy & Webhooks

## Branch Model
- **main**: Production environment.
- **develop**: Staging environment.
- **feature/***: New features.
- **hotfix/***: Emergency fixes.

## GitHub Branch Protection
- **main**: Require 2 PR reviews, CI passing, no force-push.

## Webhook Config
- **Payload URL**: `http://JENKINS_IP:8080/github-webhook/`
- **Events**: Push, Pull Request

## Jenkins Multibranch Pipeline
- **feature/*** -> Tests only.
- **develop** -> Deploy to staging namespace.
- **main** -> Deploy to production (manual approval required).
"""

app_properties = """
# Spring Boot Actuator
management.endpoints.web.exposure.include=health,info,prometheus,metrics,loggers
management.endpoint.health.show-details=always
management.endpoint.health.group.liveness.include=diskSpace,ping
management.endpoint.health.group.readiness.include=db,redis,downstream-service
"""

base = "c:/dr-chaos-platform"
write_file(f"{base}/app/Dockerfile", dockerfile)
write_file(f"{base}/app/Jenkinsfile", jenkinsfile)
write_file(f"{base}/.github/workflows/lint.yaml", github_lint)
write_file(f"{base}/disaster-recovery/git-strategy.md", git_strategy)
write_file(f"{base}/app/src/main/resources/application.properties", app_properties)

print("App and CI/CD files generated successfully.")
