# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

variable "centos7_amis" {
    description = "Centos 7 AMI IDs for various AWS regions"
    type = "map"
    default = {
        us-east-1 = "ami-6d1c2007"
        us-west-1 = "ami-af4333cf"
        us-west-2 = "ami-3ecc8f46"
    }
}
