variable "availability_zone" {
  description = "AZ for the subnet (a, b, or c)"
}

variable "cidr_block" {
  description = "CIDR block for this subnet"
}

variable "nat_gateway_id" {
  description = "ID of NAT gateway to route outgoing internet traffic through"
}

variable "taskcluster_vpc_cidr" {
  description = "CIDR block of the Taskcluster VPC in the same AWS region"
}

variable "vpn_gateway_id" {
  description = "ID of VPN gateway to send relevant traffic through"
}

variable "vpc_id" {
  description = "ID of VPC in which the subnet will reside"
}
