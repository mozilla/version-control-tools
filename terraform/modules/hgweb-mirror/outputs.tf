output "instance_id" {
  description = "Instance ID for the mirror"
  value = "${aws_instance.hgweb-mirror.id}"
}

output "private_ip" {
  description = "Private IP address of the mirror instance"
  value = "${aws_instance.hgweb-mirror.private_ip}"
}