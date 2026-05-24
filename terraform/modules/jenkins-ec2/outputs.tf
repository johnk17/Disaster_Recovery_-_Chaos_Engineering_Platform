output "jenkins_url" {
  value = "http://${aws_eip.jenkins_eip.public_ip}:8080"
}
