# Grab VPN gateway via the `Name` tag
# don't track this under Terraform as it
# will likely never change and would require
# work from NetOps
data "aws_vpn_gateway" "mdc-vpn-gate" {
  filter {
    name = "tag:Name"
    values = ["to-mdc's"]
  }
}

// Read the template file and fill with user info
data "template_file" "bastioninit" {
  template = "${file("${path.module}/user_data.tmpl")}"
  
  vars {
    s3_metadata_bucket = "${var.metadata_bucket_name}"
    usernames = "${join(",", var.environment_users)}"
  }
}

data "template_cloudinit_config" "bastioninit-config" {
  part {
    content = "${data.template_file.bastioninit.rendered}"
    content_type = "text/cloud-config"
  }
}

# Create a VPC for the private CI hgweb instances
resource "aws_vpc" "hgci-vpc" {
  cidr_block = "${var.cidr_block}"

  # Enable DNS lookups but do not assign DNS records
  # to new instances
  enable_dns_hostnames = false
  enable_dns_support = true

  tags {
    Name = "hgaws VPC"
  }
}

# Internet gateway for the VPC
# Facilitates access to the internet
resource "aws_internet_gateway" "hgci-internet-gateway" {
  vpc_id = "${aws_vpc.hgci-vpc.id}"

  tags {
    Name = "Internet gateway"
  }
}

# Elastic IP address for the VPC internet gateway
resource "aws_eip" "hgci-internet-eip" {
  depends_on = ["aws_internet_gateway.hgci-internet-gateway"]
  vpc = true

  tags {
    Name = "VPC Internet gateway elastic IP"
  }
}

# Route table to send traffic from the public subnet
# to the internet
resource "aws_route_table" "hgci-pub-routetable" {
  vpc_id = "${aws_vpc.hgci-vpc.id}"

  route {
    cidr_block = "10.0.0.0/10"
    gateway_id = "${data.aws_vpn_gateway.mdc-vpn-gate.id}"
  }

  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = "${aws_internet_gateway.hgci-internet-gateway.id}"
  }

  tags {
    Name = "Public route table"
  }
}

# Custom DHCP rules to query internal DNS
resource "aws_vpc_dhcp_options" "dhcp-options" {
  domain_name_servers = ["10.48.75.120", "169.254.169.253"]

  tags {
    Name = "DHCP options for internal DNS"
  }
}

resource "aws_vpc_dhcp_options_association" "dhcp-options-assoc" {
  dhcp_options_id = "${aws_vpc_dhcp_options.dhcp-options.id}"
  vpc_id = "${aws_vpc.hgci-vpc.id}"
}

# Public subnets to facilitate internet access from private subnets
module "pubsubnet-a" {
  source = "../pubsubnet"

  availability_zone = "a"
  awsregion = "${var.awsregion}"
  cidr_block = "${cidrsubnet("${var.cidr_block}", 3, 0)}"
  route_table_id = "${aws_route_table.hgci-pub-routetable.id}"
  vpc_id = "${aws_vpc.hgci-vpc.id}"
}

module "pubsubnet-b" {
  source = "../pubsubnet"

  availability_zone = "b"
  awsregion = "${var.awsregion}"
  cidr_block = "${cidrsubnet("${var.cidr_block}", 3, 1)}"
  route_table_id = "${aws_route_table.hgci-pub-routetable.id}"
  vpc_id = "${aws_vpc.hgci-vpc.id}"
}

module "pubsubnet-c" {
  source = "../pubsubnet"

  availability_zone = "c"
  awsregion = "${var.awsregion}"
  cidr_block = "${cidrsubnet("${var.cidr_block}", 3, 2)}"
  route_table_id = "${aws_route_table.hgci-pub-routetable.id}"
  vpc_id = "${aws_vpc.hgci-vpc.id}"
}

# Private subnets to hold 
module "privsubnet-a" {
  source = "../privsubnet"

  availability_zone = "a"
  awsregion = "${var.awsregion}"
  cidr_block = "${cidrsubnet("${var.cidr_block}", 3, 3)}"
  nat_gateway_id = "${module.pubsubnet-a.nat_gateway_id}"
  vpc_id = "${aws_vpc.hgci-vpc.id}"
  vpn_gateway_id = "${data.aws_vpn_gateway.mdc-vpn-gate.id}"
}

module "privsubnet-b" {
  source = "../privsubnet"

  availability_zone = "b"
  awsregion = "${var.awsregion}"
  cidr_block = "${cidrsubnet("${var.cidr_block}", 3, 4)}"
  nat_gateway_id = "${module.pubsubnet-b.nat_gateway_id}"
  vpc_id = "${aws_vpc.hgci-vpc.id}"
  vpn_gateway_id = "${data.aws_vpn_gateway.mdc-vpn-gate.id}"
}

module "privsubnet-c" {
  source = "../privsubnet"

  availability_zone = "c"
  awsregion = "${var.awsregion}"
  cidr_block = "${cidrsubnet("${var.cidr_block}", 3, 5)}"
  nat_gateway_id = "${module.pubsubnet-c.nat_gateway_id}"
  vpc_id = "${aws_vpc.hgci-vpc.id}"
  vpn_gateway_id = "${data.aws_vpn_gateway.mdc-vpn-gate.id}"
}

module "bastion" {
  source = "../bastion"

  awsregion = "${var.awsregion}"
  availability_zone = "a"
  bastion_ami = "${var.bastion_ami}"
  environment_users = "${var.environment_users}"
  subnet_id = "${module.pubsubnet-a.subnet_id}"
  user_data = "${data.template_cloudinit_config.bastioninit-config.rendered}"
  vpc_id = "${aws_vpc.hgci-vpc.id}"
}

# Create a security group for the private CI instances
# Use these rules to INCLUDE traffic
resource "aws_security_group" "hgci-securitygroup" {
  name = "hgci-securitygroup"
  description = "Set security rules for private CI-only hgweb instances"
  vpc_id = "${aws_vpc.hgci-vpc.id}"

  # Incoming rules
  ingress {
    description = "SSH to instance from Bastion host"

    from_port = 22
    protocol = "tcp"
    to_port = 22
    security_groups = [
      "${module.bastion.security_group_id}",
    ]
  }

  ingress {
    description = "HTTP between Bastion (TESTING)"

    from_port = 80
    to_port = 80
    protocol = "tcp"

    security_groups = [
      "${module.bastion.security_group_id}"
    ]
  }

  ingress {
    description = "HTTPS between Bastion (TESTING)"

    from_port = 443
    to_port = 443
    protocol = "tcp"

    security_groups = [
      "${module.bastion.security_group_id}"
    ]
  }

  # Outgoing rules
  egress {
    description = "Allow all outgoing"

    from_port = 0
    protocol = "-1"
    to_port = 0

    cidr_blocks = [
      "0.0.0.0/0"
    ]
  }

  tags {
    Name = "CI-only hgweb security group"
  }
}

module "test-hgweb-mirror" {
  source = "../hgweb-mirror"

  awsregion = "${var.awsregion}"
  availability_zone = "a"
  environment_users = "${var.environment_users}"
  mirror_ami = "${var.mirror_ami}"
  security_group_ids = [
    "${aws_security_group.hgci-securitygroup.id}",
  ]
  subnet_id = "${module.privsubnet-a.subnet_id}"
  user_data = "${data.template_cloudinit_config.bastioninit-config.rendered}"
}

# Create a network ACL for the VPC
# Use these rules to EXCLUDE traffic
resource "aws_network_acl" "hgci-networkacl" {
  vpc_id = "${aws_vpc.hgci-vpc.id}"

  subnet_ids = [
    "${module.privsubnet-a.subnet_id}",
    "${module.privsubnet-b.subnet_id}",
    "${module.privsubnet-c.subnet_id}",
    "${module.pubsubnet-a.subnet_id}",
    "${module.pubsubnet-b.subnet_id}",
    "${module.pubsubnet-c.subnet_id}",
  ]

  # Allow SSH in from the world
  ingress {
    action = "allow"
    cidr_block = "0.0.0.0/0"
    from_port = 22
    protocol = "tcp"
    rule_no = 10
    to_port = 22
  }
  
  # Allow outgoing https
  egress {
    cidr_block = "${var.cidr_block}"
    action = "allow"
    from_port = 443
    protocol = "tcp"
    rule_no = 20
    to_port = 443
  }
  
  # Allow outgoing SSH
  egress {
    cidr_block = "${var.cidr_block}"
    action = "allow"
    from_port = 22
    protocol = "tcp"
    rule_no = 30
    to_port = 22
  }
  
  # Deny everything else
  ingress {
    action = "deny"
    cidr_block = "0.0.0.0/0"
    from_port = 0
    protocol = "-1"
    rule_no = 100
    to_port = 0
  }

  tags {
    Name = "hg AWS network ACLs"
  }
}