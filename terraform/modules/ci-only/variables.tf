variable "cidr_block" {
  description = "CIDR block for the VPC"
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

variable "taskcluster_vpc_cidr" {
  description = "CIDR block of the Taskcluster VPC in the same AWS region"
}
