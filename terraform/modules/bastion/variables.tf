variable "availability_zone" {
  description = "Availability zone for this Bastion host (a, b, or c)"
}

variable "awsregion" {
  description = "AWS region of the VPC"
}

variable "bastion_ami" {
  description = "AMI ID for Bastion instances"
}

variable "environment_users" {
  description = "Authorized users within VCS environments"
  type = "list"
}

variable "subnet_id" {
  description = "ID of subnet in which to launch VPC"
}

variable "user_data" {
  description = "User data used to bootstrap instances with cloud-init"
}

variable "vpc_id" {
  description = "ID of VPC in which to launch Bastion host"
}
