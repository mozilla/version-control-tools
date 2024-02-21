# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

data "aws_region" "current" {
}

# Grab VPN gateway via the `Name` tag
# don't track this under Terraform as it
# will likely never change and would require
# work from NetOps
data "aws_vpn_gateway" "mdc-vpn-gate" {
  filter {
    name   = "tag:Name"
    values = ["to-mdc's", "to-mdc"]
  }
}

# Create a VPC for the private CI hgweb instances
resource "aws_vpc" "hgci-vpc" {
  cidr_block = var.cidr_block

  # Enable DNS
  enable_dns_hostnames = true
  enable_dns_support   = true

  tags = {
    Name = "hgaws VPC"
  }
}

# Internet gateway for the VPC
# Facilitates access to the internet
resource "aws_internet_gateway" "hgci-internet-gateway" {
  vpc_id = aws_vpc.hgci-vpc.id

  tags = {
    Name = "Internet gateway"
  }
}

# Elastic IP address for the VPC internet gateway
resource "aws_eip" "hgci-internet-eip" {
  depends_on = [aws_internet_gateway.hgci-internet-gateway]
  vpc        = true

  tags = {
    Name = "VPC Internet gateway elastic IP"
  }
}

# Route table to send traffic from the public subnet
# to the internet
resource "aws_route_table" "hgci-pub-routetable" {
  vpc_id = aws_vpc.hgci-vpc.id

  route {
    cidr_block = "10.0.0.0/10"
    gateway_id = data.aws_vpn_gateway.mdc-vpn-gate.id
  }

  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.hgci-internet-gateway.id
  }

  tags = {
    Name = "Public route table"
  }
}

# Custom DHCP rules to query internal DNS
resource "aws_vpc_dhcp_options" "dhcp-options" {
  domain_name_servers = ["10.48.75.120"]

  tags = {
    Name = "DHCP options for internal DNS"
  }
}

resource "aws_vpc_dhcp_options_association" "dhcp-options-assoc" {
  dhcp_options_id = aws_vpc_dhcp_options.dhcp-options.id
  vpc_id          = aws_vpc.hgci-vpc.id
}

# Public subnets to facilitate internet access from private subnets
module "pubsubnet-a" {
  source = "../pubsubnet"

  availability_zone = "a"
  cidr_block        = cidrsubnet(var.cidr_block, 3, 0)
  route_table_id    = aws_route_table.hgci-pub-routetable.id
  vpc_id            = aws_vpc.hgci-vpc.id
}

module "pubsubnet-b" {
  source = "../pubsubnet"

  availability_zone = "b"
  cidr_block        = cidrsubnet(var.cidr_block, 3, 1)
  route_table_id    = aws_route_table.hgci-pub-routetable.id
  vpc_id            = aws_vpc.hgci-vpc.id
}

# Private subnets to hold
module "privsubnet-a" {
  source = "../privsubnet"

  availability_zone    = "a"
  cidr_block           = cidrsubnet(var.cidr_block, 3, 3)
  nat_gateway_id       = module.pubsubnet-a.nat_gateway_id
  taskcluster_vpc_cidr = var.taskcluster_vpc_cidr
  vpc_id               = aws_vpc.hgci-vpc.id
  vpn_gateway_id       = data.aws_vpn_gateway.mdc-vpn-gate.id
}

module "privsubnet-b" {
  source = "../privsubnet"

  availability_zone    = "b"
  cidr_block           = cidrsubnet(var.cidr_block, 3, 4)
  nat_gateway_id       = module.pubsubnet-b.nat_gateway_id
  taskcluster_vpc_cidr = var.taskcluster_vpc_cidr
  vpc_id               = aws_vpc.hgci-vpc.id
  vpn_gateway_id       = data.aws_vpn_gateway.mdc-vpn-gate.id
}

resource "aws_security_group" "lb-securitygroup" {
  name        = "lb-securitygroup"
  description = "Set security rules for application load balancer"
  vpc_id      = aws_vpc.hgci-vpc.id

  tags = {
    Name = "load balancer security group"
  }
}

resource "aws_security_group_rule" "rule-hgvpc-lb" {
  description       = "Allow traffic from our VPC to LB listener port"
  security_group_id = aws_security_group.lb-securitygroup.id
  type              = "ingress"
  from_port         = 443
  protocol          = "tcp"
  to_port           = 443
  cidr_blocks       = [aws_vpc.hgci-vpc.cidr_block]
}

resource "aws_security_group_rule" "rule-tcvpc-lb" {
  description       = "Allow traffic from Taskcluster VPC to LB listener port"
  security_group_id = aws_security_group.lb-securitygroup.id
  type              = "ingress"
  from_port         = 443
  protocol          = "tcp"
  to_port           = 443
  cidr_blocks       = [var.taskcluster_vpc_cidr]
}

resource "aws_security_group_rule" "rule-lb-listener" {
  description              = "Allow traffic to instances on health check/listener port (80)"
  security_group_id        = aws_security_group.lb-securitygroup.id
  type                     = "egress"
  from_port                = 80
  protocol                 = "tcp"
  to_port                  = 80
  source_security_group_id = aws_security_group.hgci-securitygroup.id
}

# Create a security group for the private CI instances
# Use these rules to INCLUDE traffic
resource "aws_security_group" "hgci-securitygroup" {
  name        = "hgci-securitygroup"
  description = "Set security rules for private CI-only hgweb instances"
  vpc_id      = aws_vpc.hgci-vpc.id

  tags = {
    Name = "CI-only hgweb security group"
  }
}

resource "aws_security_group_rule" "rule-mozvpn-hgci" {
  description       = "SSH to instances from MozVPN"
  security_group_id = aws_security_group.hgci-securitygroup.id
  type              = "ingress"
  from_port         = 22
  protocol          = "tcp"
  to_port           = 22
  cidr_blocks = [
    "10.48.240.0/23",
    "10.48.242.0/23",
    "10.50.240.0/23",
    "10.50.242.0/23",
    "10.64.0.0/16",
  ]
}

resource "aws_security_group_rule" "rule-tcvpc-hgci" {
  description       = "All traffic from Taskcluster VPC"
  security_group_id = aws_security_group.hgci-securitygroup.id
  type              = "ingress"
  from_port         = 0
  to_port           = 0
  protocol          = "-1"

  cidr_blocks = [
    var.taskcluster_vpc_cidr,
  ]
}

resource "aws_security_group_rule" "rule-allowself" {
  description       = "All traffic within group"
  security_group_id = aws_security_group.hgci-securitygroup.id
  type              = "ingress"
  from_port         = 0
  protocol          = "-1"
  to_port           = 0
  self              = true
}

resource "aws_security_group_rule" "rule-allowout" {
  description       = "Allow all outgoing"
  security_group_id = aws_security_group.hgci-securitygroup.id
  type              = "egress"
  from_port         = 0
  protocol          = "-1"
  to_port           = 0

  cidr_blocks = [
    "0.0.0.0/0",
  ]
}

resource "aws_security_group_rule" "rule-hgci-lb" {
  description              = "All traffic from load balancers"
  security_group_id        = aws_security_group.hgci-securitygroup.id
  type                     = "ingress"
  from_port                = 0
  protocol                 = "-1"
  to_port                  = 0
  source_security_group_id = aws_security_group.lb-securitygroup.id
}

resource "aws_acm_certificate" "hgcert" {
  domain_name       = "*.hgmointernal.net"
  validation_method = "DNS"

  lifecycle {
    create_before_destroy = true
  }

  tags = {
    Name = "hg certificate"
  }
}

# Load balancer for traffic in this region
resource "aws_lb" "internal-lb" {
  name               = "${data.aws_region.current.name}-lb"
  internal           = true
  load_balancer_type = "application"
  security_groups    = [aws_security_group.lb-securitygroup.id]
  subnets = [
    module.privsubnet-a.subnet_id,
    module.privsubnet-b.subnet_id,
  ]

  tags = {
    Name = "${data.aws_region.current.name} hg load balancer"
  }
}

resource "aws_lb_target_group" "http-mirror-target-group" {
  name     = "${data.aws_region.current.name}-hg-mirrors"
  port     = 80
  protocol = "HTTP"
  vpc_id   = aws_vpc.hgci-vpc.id

  # Use `/mozilla-central` here since using `/` will cause
  # many errors when the LB follows links on the home page
  health_check {
    enabled             = true
    interval            = 30
    path                = "/mozilla-central"
    port                = "traffic-port"
    healthy_threshold   = 5
    unhealthy_threshold = 2
    timeout             = 5
    matcher             = "200"
  }
}

resource "aws_lb_listener" "mirror-https-listener" {
  load_balancer_arn = aws_lb.internal-lb.arn
  port              = 443
  protocol          = "HTTPS"
  ssl_policy        = "ELBSecurityPolicy-2016-08"
  certificate_arn   = aws_acm_certificate.hgcert.arn

  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.http-mirror-target-group.arn
  }
}

resource "aws_instance" "hgweb-backup" {
  # Create this instance if `backup_node` is non-zero
  count = var.backup_node

  ami                    = var.mirror_ami
  instance_type          = "c5d.2xlarge"
  subnet_id              = module.privsubnet-b.subnet_id
  vpc_security_group_ids = [
    aws_security_group.hgci-securitygroup.id,
  ]
  ebs_optimized          = true

  user_data = file("${path.module}/user_data.yml")

  root_block_device {
    delete_on_termination = false
    volume_size           = 1000
    volume_type           = "standard"
  }

  lifecycle {
    ignore_changes = [user_data]
  }

  tags = {
    Name = "repo data backup instance"
  }
}

# Create a network ACL for the VPC
# Use these rules to EXCLUDE traffic
resource "aws_network_acl" "hgci-networkacl" {
  vpc_id = aws_vpc.hgci-vpc.id

  subnet_ids = [
    module.privsubnet-a.subnet_id,
    module.privsubnet-b.subnet_id,
    module.pubsubnet-a.subnet_id,
    module.pubsubnet-b.subnet_id,
  ]

  ingress {                                                                                                                                                                                 
      action          = "allow"                                                                                                                                                     
      cidr_block      = "0.0.0.0/0"                                                  
      from_port       = 0                                                                                                                                                           
      icmp_code       = 0                                                            
      icmp_type       = 0                                                            
      protocol        = "-1"                                                         
      rule_no         = 100                                                                                                                                                         
      to_port         = 0                                                            
  }

  # Allow outgoing SSH
  egress {
      action          = "allow"                                                                                                                                                     
      cidr_block      = "0.0.0.0/0"                                                                                                                                                 
      from_port       = 0                                                                                                                                                           
      icmp_code       = 0                                                                                                                                                           
      icmp_type       = 0                                                                                                                                                           
      protocol        = "-1"                                                                                                                                                        
      rule_no         = 100                                                                                                                                                         
      to_port         = 0
  }

  tags = {
    Name = "hg AWS network ACLs"
  }
}

