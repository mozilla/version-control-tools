# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

variable "availability_zone" {
  description = "AZ in which to deploy the instance (a, b or c)"
}

variable "environment_users" {
  description = "Authorized users within VCS environmentss"
}

variable "mirror_ami" {
  description = "AMI ID for mirror instances"
}

variable "security_group_ids" {
  description = "IDs of security groups which apply to this instance"
  type = "list"
}

variable "subnet_id" {
  description = "Subnet in which to deploy the instance"
}

variable "user_data" {
  description = "User data used to bootstrap instances with cloud-init"
}
