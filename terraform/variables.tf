# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

variable "centos7_amis" {
    description = "Centos 7 AMI IDs for various AWS regions"
    type = "map"
    default = {
        us-east-1 = "ami-02eac2c0129f6376b"
        us-east-2 = "ami-0f2b4fc905b0bd1f1"
        us-west-1 = "ami-074e2d6769f445be5"
        us-west-2 = "ami-01ed306a12b7d1c96"
    }
}
