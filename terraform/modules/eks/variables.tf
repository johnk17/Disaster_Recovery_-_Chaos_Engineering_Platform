variable "cluster_name" {
  type    = string
  default = "dr-chaos-eks"
}
variable "vpc_id" {
  type = string
}
variable "private_subnets" {
  type = list(string)
}
variable "public_subnets" {
  type = list(string)
}
