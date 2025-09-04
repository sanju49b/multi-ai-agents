pipeline{
    agent any

    environment {
        SONAR_PROJECT_KEY = 'multiagentai'
        SONAR_SCANNER_HOME = tool 'sonarqube'
        AWS_REGION = 'eu-north-1'
        ECR_REPO = 'multiagent'
        IMAGE_TAG = "${BUILD_NUMBER}"  // Use unique tag per build
        CLUSTER_NAME = 'multi-ai-agent-cluster1'
        SERVICE_NAME = 'multiaiagentdef-service-7wxh1cwd'
        TASK_DEFINITION_FAMILY = 'multiaiagentdef'
    }

    stages{
        stage('Cloning Github repo to Jenkins'){
            steps{
                script{
                    echo 'Cloning Github repo to Jenkins............'
                    checkout scmGit(branches: [[name: '*/main']], extensions: [], userRemoteConfigs: [[credentialsId: 'github-token', url: 'https://github.com/data-guru0/MULTI-AI-AGENT-PROJECTS.git']])
                }
            }
        }

        stage('SonarQube Analysis'){
            steps {
                withCredentials([string(credentialsId: 'sonarqube-token', variable: 'SONAR_TOKEN')]) {
                    withSonarQubeEnv('sonarqube') {
                        sh """
                        ${SONAR_SCANNER_HOME}/bin/sonar-scanner \
                        -Dsonar.projectKey=${SONAR_PROJECT_KEY} \
                        -Dsonar.sources=. \
                        -Dsonar.host.url=http://sonarqube-dind:9000 \
                        -Dsonar.login=${SONAR_TOKEN}
                        """
                    }
                }
            }
        }

        stage('Build and Push Docker Image to ECR') {
            steps {
                withCredentials([[$class: 'AmazonWebServicesCredentialsBinding', credentialsId: 'aws token']]) {
                    script {
                        def accountId = sh(script: "aws sts get-caller-identity --query Account --output text", returnStdout: true).trim()
                        def ecrUrl = "${accountId}.dkr.ecr.${env.AWS_REGION}.amazonaws.com/${env.ECR_REPO}"

                        sh """
                        # Login to ECR
                        aws ecr get-login-password --region ${AWS_REGION} | docker login --username AWS --password-stdin ${ecrUrl}
                        
                        # Build image
                        docker build -t ${env.ECR_REPO}:${IMAGE_TAG} .
                        
                        # Tag for both build number and latest
                        docker tag ${env.ECR_REPO}:${IMAGE_TAG} ${ecrUrl}:${IMAGE_TAG}
                        docker tag ${env.ECR_REPO}:${IMAGE_TAG} ${ecrUrl}:latest
                        
                        # Push both tags
                        docker push ${ecrUrl}:${IMAGE_TAG}
                        docker push ${ecrUrl}:latest
                        
                        echo "Successfully pushed image with tags: ${IMAGE_TAG} and latest"
                        """
                    }
                }
            }
        }

        stage('Deploy to ECS Fargate') {
            steps {
                withCredentials([[$class: 'AmazonWebServicesCredentialsBinding', credentialsId: 'aws token']]) {
                    script {
                        def accountId = sh(script: "aws sts get-caller-identity --query Account --output text", returnStdout: true).trim()
                        def ecrUrl = "${accountId}.dkr.ecr.${env.AWS_REGION}.amazonaws.com/${env.ECR_REPO}"
                        
                        sh """
                        # Get current task definition and extract environment variables
                        CURRENT_ENV=\$(aws ecs describe-task-definition --task-definition ${TASK_DEFINITION_FAMILY} --region ${AWS_REGION} --query 'taskDefinition.containerDefinitions[0].environment' --output json)
                        EXECUTION_ROLE_ARN=\$(aws ecs describe-task-definition --task-definition ${TASK_DEFINITION_FAMILY} --region ${AWS_REGION} --query 'taskDefinition.executionRoleArn' --output text)
                        
                        if [ "\$EXECUTION_ROLE_ARN" = "None" ]; then
                            EXECUTION_ROLE_ARN="arn:aws:iam::${accountId}:role/ecsTaskExecutionRole"
                        fi
                        
                        # Create new task definition with updated image but keep existing environment variables
                        NEW_TASK_DEFINITION=\$(aws ecs register-task-definition \\
                          --family ${TASK_DEFINITION_FAMILY} \\
                          --execution-role-arn \$EXECUTION_ROLE_ARN \\
                          --network-mode awsvpc \\
                          --requires-compatibilities FARGATE \\
                          --cpu 2048 \\
                          --memory 6144 \\
                          --container-definitions "[{
                            \\"name\\": \\"aiagent\\",
                            \\"image\\": \\"${ecrUrl}:${IMAGE_TAG}\\",
                            \\"cpu\\": 0,
                            \\"portMappings\\": [
                              {
                                \\"containerPort\\": 80,
                                \\"hostPort\\": 80,
                                \\"protocol\\": \\"tcp\\",
                                \\"name\\": \\"aiagent-80-tcp\\",
                                \\"appProtocol\\": \\"http\\"
                              },
                              {
                                \\"containerPort\\": 8501,
                                \\"hostPort\\": 8501,
                                \\"protocol\\": \\"tcp\\",
                                \\"name\\": \\"aiagent-8501-tcp\\"
                              },
                              {
                                \\"containerPort\\": 9999,
                                \\"hostPort\\": 9999,
                                \\"protocol\\": \\"tcp\\",
                                \\"name\\": \\"aiagent-9999-tcp\\"
                              }
                            ],
                            \\"essential\\": true,
                            \\"environment\\": \$CURRENT_ENV,
                            \\"logConfiguration\\": {
                              \\"logDriver\\": \\"awslogs\\",
                              \\"options\\": {
                                \\"awslogs-create-group\\": \\"true\\",
                                \\"awslogs-group\\": \\"/ecs/${TASK_DEFINITION_FAMILY}\\",
                                \\"awslogs-region\\": \\"${AWS_REGION}\\",
                                \\"awslogs-stream-prefix\\": \\"ecs\\"
                              }
                            }
                          }]" \\
                          --region ${AWS_REGION} \\
                          --query 'taskDefinition.revision' \\
                          --output text)
                        
                        echo "Created new task definition revision: \$NEW_TASK_DEFINITION"
                        
                        # Update the service to use the new task definition
                        aws ecs update-service \\
                          --cluster ${CLUSTER_NAME} \\
                          --service ${SERVICE_NAME} \\
                          --task-definition ${TASK_DEFINITION_FAMILY}:\$NEW_TASK_DEFINITION \\
                          --region ${AWS_REGION}
                        
                        echo "Updated service to use new task definition"
                        
                        # Wait for deployment to complete
                        echo "Waiting for deployment to stabilize..."
                        aws ecs wait services-stable \\
                          --cluster ${CLUSTER_NAME} \\
                          --services ${SERVICE_NAME} \\
                          --region ${AWS_REGION}
                        
                        echo "Deployment completed successfully!"
                        
                        # Get the public IP for verification
                        TASK_ARN=\$(aws ecs list-tasks --cluster ${CLUSTER_NAME} --service-name ${SERVICE_NAME} --region ${AWS_REGION} --query 'taskArns[0]' --output text)
                        PUBLIC_IP=\$(aws ecs describe-tasks --cluster ${CLUSTER_NAME} --tasks \$TASK_ARN --region ${AWS_REGION} --query 'tasks[0].attachments[0].details[?name==\`networkInterfaceId\`].value' --output text | xargs -I {} aws ec2 describe-network-interfaces --network-interface-ids {} --region ${AWS_REGION} --query 'NetworkInterfaces[0].Association.PublicIp' --output text)
                        
                        echo "Application deployed successfully!"
                        echo "Streamlit app should be accessible at: http://\$PUBLIC_IP:8501"
                        """
                    }
                }
            }
        }
    }
    
    post {
        always {
            // Clean up Docker images to save space
            sh 'docker system prune -f'
        }
        success {
            echo 'Pipeline completed successfully!'
        }
        failure {
            echo 'Pipeline failed!'
        }
    }
}