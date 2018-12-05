output "subnet_id" {
  description = "ID of the new subnet"
  value = "${aws_subnet.privsubnet.id}"
}
