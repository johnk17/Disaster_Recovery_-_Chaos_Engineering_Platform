variable "vpc_id" {
  type = string
}
variable "subnet_id" {
  type = string
}
variable "jenkins_allowed_ip" {
  type    = string
  default = "0.0.0.0/0"
}
