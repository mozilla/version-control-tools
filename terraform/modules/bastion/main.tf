# Bastion Host
# Set up a bastion host in one of the public subnets
# to facilitate deployment and SSH access to the mirrors
# in the private subnets
resource "aws_security_group" "hgci-bastion-securitygroup" {
  name = "hgci-bastion-securitygroup"
  description = "Security group for Bastion hosts"
  vpc_id = "${var.vpc_id}"

  ingress {
    description = "SSH access in from MozVPN"
    from_port = 22
    protocol = "tcp"
    to_port = 22

    cidr_blocks = [
      "10.48.240.0/23",
      "10.48.242.0/23",
      "10.50.240.0/23",
      "10.50.242.0/23",
      "10.64.0.0/16",
    ]
  }

  egress {
    description = "Outgoing traffic permitted"
    from_port = 0
    to_port = 0
    protocol = "-1"
    cidr_blocks = [
      "0.0.0.0/0",
    ]
  }

  tags {
    Name = "Bastion host security group"
  }
}

resource "aws_instance" "hgci-bastion" {
  ami = "${var.bastion_ami}"
  availability_zone = "${var.awsregion}${var.availability_zone}"
  instance_type = "t2.micro"
  subnet_id = "${var.subnet_id}"
  vpc_security_group_ids = [
    "${aws_security_group.hgci-bastion-securitygroup.id}"
  ]

  user_data = "${var.user_data}"

  tags {
    Name = "Bastion host A"
  }
}
