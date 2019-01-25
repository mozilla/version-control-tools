# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

variable "availability_zone" {
  description = "AZ for the subnet ('a', 'b' or 'c')"
}

variable "cidr_block" {
  description = "CIDR block for this subnet"
}

variable "route_table_id" {
  description = "ID of route table to associate with this subnet"
}

variable "vpc_id" {
  description = "ID of VPC in which the subnet will reside"
}
