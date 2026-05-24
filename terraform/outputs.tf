output "cluster_endpoint" {
  value = module.eks.cluster_endpoint
}
output "velero_s3_bucket" {
  value = aws_s3_bucket.velero.id
}
output "jenkins_url" {
  value = module.jenkins.jenkins_url
}
output "kubeconfig_command" {
  value = "aws eks update-kubeconfig --region us-east-1 --name ${module.eks.cluster_name}"
}
