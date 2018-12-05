resource "aws_subnet" "privsubnet" {
  availability_zone = "${var.awsregion}${var.availability_zone}"
  cidr_block = "${var.cidr_block}"
  map_public_ip_on_launch = false
  vpc_id = "${var.vpc_id}"

  tags {
    Name = "Private subnet ${var.availability_zone}"
  }
}


resource "aws_route_table" "routetable" {
  vpc_id = "${var.vpc_id}"

  route {
    cidr_block = "0.0.0.0/0"
    nat_gateway_id = "${var.nat_gateway_id}"
  }

  route {
    cidr_block = "10.0.0.0/10"
    gateway_id = "${var.vpn_gateway_id}"
  }

  tags {
    Name = "Private route table ${var.availability_zone}"
  }
}

resource "aws_route_table_association" "route_associate" {
  route_table_id = "${aws_route_table.routetable.id}"
  subnet_id = "${aws_subnet.privsubnet.id}"
}
