output "nat_gateway_id" {
  description = "ID of NAT gateway attached to this subnet"
  value = "${aws_nat_gateway.nat.id}"
}

output "subnet_id" {
  description = "ID of the new subnet"
  value = "${aws_subnet.pubsubnet.id}"
}
