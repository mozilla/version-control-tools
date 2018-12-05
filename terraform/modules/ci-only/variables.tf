variable "awsregion" {
  description = "AWS region in which the VPC is deployed"
}

variable "bastion_ami" {
  description = "AMI ID for Bastion instances"
}

variable "cidr_block" {
  description = "CIDR prefix for the VPC. Corresponds to the 16 bit netmask of the VPC"
}

variable "environment_users" {
  description = "List of users in this environment"
  type = "list"
}

variable "metadata_bucket_name" {
  description = "Name of the metadata bucket"
}

variable "mirror_ami" {
  description = "AMI ID for mirror instances"
}
