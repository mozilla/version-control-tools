output "security_group_id" {
  description = "ID of the security group for Bastion hosts"
  value = "${aws_security_group.hgci-bastion-securitygroup.id}"
}
