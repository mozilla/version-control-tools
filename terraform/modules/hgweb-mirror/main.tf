resource "aws_instance" "hgweb-mirror" {
  ami = "${var.mirror_ami}"
  instance_type = "c5d.2xlarge"
  subnet_id = "${var.subnet_id}"
  vpc_security_group_ids = ["${var.security_group_ids}"]

  user_data = "${var.user_data}"
  
  root_block_device {
    delete_on_termination = true
    volume_size = 100
    volume_type = "standard"
  }

  tags {
    Name = "hgweb instance"
  }
}
