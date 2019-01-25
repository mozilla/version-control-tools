# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

output "nat_gateway_id" {
  description = "ID of NAT gateway attached to this subnet"
  value = "${aws_nat_gateway.nat.id}"
}

output "subnet_id" {
  description = "ID of the new subnet"
  value = "${aws_subnet.pubsubnet.id}"
}
