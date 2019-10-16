# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

output "instance_id" {
  description = "Instance ID for the mirror"
  value       = aws_instance.hgweb-mirror.id
}

output "private_ip" {
  description = "Private IP address of the mirror instance"
  value       = aws_instance.hgweb-mirror.private_ip
}

