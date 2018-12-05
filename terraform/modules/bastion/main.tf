# Bastion Host
# Set up a bastion host in one of the public subnets
# to facilitate deployment and SSH access to the mirrors
# in the private subnets
resource "aws_security_group" "hgci-bastion-securitygroup" {
  name = "hgci-bastion-securitygroup"
  description = "Security group for Bastion hosts"
  vpc_id = "${var.vpc_id}"

  ingress {
    description = "SSH access in"
    from_port = 22
    protocol = "tcp"
    to_port = 22

    cidr_blocks = [
      "0.0.0.0/0",
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

resource "aws_eip" "hgci-bastion-eip" {
  depends_on = ["aws_instance.hgci-bastion"]
  instance = "${aws_instance.hgci-bastion.id}"
  vpc = true

  tags {
    Name = "Bastion host elastic IP"
  }
}
