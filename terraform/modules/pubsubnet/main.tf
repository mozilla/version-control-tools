resource "aws_subnet" "pubsubnet" {
  availability_zone = "${var.awsregion}${var.availability_zone}"
  cidr_block = "${var.cidr_block}"
  map_public_ip_on_launch = false
  vpc_id = "${var.vpc_id}"

  tags {
    Name = "Public subnet ${var.availability_zone}"
  }
}

resource "aws_eip" "nat-eip" {
  vpc = true

  tags {
    Name = "NAT gateway ${var.availability_zone} elastic IP"
  }
}

resource "aws_nat_gateway" "nat" {
  allocation_id = "${aws_eip.nat-eip.id}"
  subnet_id = "${aws_subnet.pubsubnet.id}"

  tags {
    Name = "NAT gateway ${var.availability_zone}"
  }
}

resource "aws_route_table_association" "pubroute" {
  route_table_id = "${var.route_table_id}"
  subnet_id = "${aws_subnet.pubsubnet.id}"
}
