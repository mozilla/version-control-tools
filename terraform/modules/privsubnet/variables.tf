# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

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
