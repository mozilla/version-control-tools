# Configure the S3 remote state backend
terraform {
  required_version = ">= 0.11.0"

  backend "s3" {
    acl = "private"
    bucket = "hgaws-metadata"
    encrypt = true
    key = "tfstate/terraform.tfstate"
    profile = "hgaws"
    region = "us-west-2"
  }
}

data "terraform_remote_state" "remotestate" {
  backend = "s3"

  config {
    acl = "private"
    bucket = "hgaws-metadata"
    key = "tfstate/terraform.tfstate"
    profile = "hgaws"
    region = "us-west-2"
  }
}

# An annoying technicality where we need to declare the
# default provider, otherwise we will be prompted when
# running `terraform apply`. See link for more info
# https://github.com/terraform-providers/terraform-provider-aws/issues/1043
provider "aws" {
  region = "us-west-2"
  profile = "hgaws"
}

# Configure the "AWS" providers.
# Credentials for the AWS account should be set in the
# ~/.aws/credentials file, in the `hgaws` profile
provider "aws" {
  alias = "awsprovider-us-west-1"
  region = "us-west-1"
  profile = "hgaws"
}

provider "aws" {
  alias = "awsprovider-us-west-2"
  region = "us-west-2"
  profile = "hgaws"
}

provider "aws" {
  alias = "awsprovider-us-east-1"
  region = "us-east-1"
  profile = "hgaws"
}

provider "aws" {
  alias = "awsprovider-us-east-2"
  region = "us-east-2"
  profile = "hgaws"
}

provider "aws" {
  alias = "awsprovider-eu-central-1"
  region = "eu-central-1"
  profile = "hgaws"
}

# Configure a bucket to hold various metadata (remote state, etc)
resource "aws_s3_bucket" "metadata-bucket" {
  bucket = "hgaws-metadata"
  acl = "private"

  versioning {
    enabled = true
  }

  tags {
    Name = "Metadata bucket for VCS"
  }
}

# Set up valid users within this environment
resource "aws_iam_user" "user-cosheehan" {
  name = "cosheehan"
}

# This user is used to upload to S3.
resource "aws_iam_user" "hgbundler" {
  name = "hgbundler"
}

# Set an IAM policy for the remote state bucket and key
data "aws_iam_policy_document" "metadata-bucket-policy-definition" {
  statement {
    principals {
      type = "AWS"
      identifiers = [
        "${aws_iam_user.user-cosheehan.arn}",
      ]
    }
    effect = "Allow"
    actions = [
      "s3:ListBucket",
    ]
    resources = [
      "${aws_s3_bucket.metadata-bucket.arn}",
    ]
  }

  statement {
    principals {
      type = "AWS"
      identifiers = [
        "${aws_iam_user.user-cosheehan.arn}",
      ]
    }
    effect = "Allow"
    actions = [
      "s3:GetObject",
      "s3:PutObject",
    ]
    resources = [
      "${aws_s3_bucket.metadata-bucket.arn}/tfstate/terraform.tfstate",
    ]
  }
}

resource "aws_s3_bucket_policy" "metadata-bucket-policy" {
  provider = "aws.awsprovider-us-west-2"
  bucket = "${aws_s3_bucket.metadata-bucket.bucket}"
  policy = "${data.aws_iam_policy_document.metadata-bucket-policy-definition.json}"
}

# Configure S3 buckets for bundles and caching
module "s3-east1" {
  source = "./modules/s3"
  bundler_arn = "${aws_iam_user.hgbundler.arn}"

  providers = {
    aws = "aws.awsprovider-us-east-1"
  }
}

module "s3-east2" {
  source = "./modules/s3"
  bundler_arn = "${aws_iam_user.hgbundler.arn}"

  providers = {
    aws = "aws.awsprovider-us-east-2"
  }
}

module "s3-west1" {
  source = "./modules/s3"
  bundler_arn = "${aws_iam_user.hgbundler.arn}"

  providers = {
    aws = "aws.awsprovider-us-west-1"
  }
}

module "s3-west2" {
  source = "./modules/s3"
  bundler_arn = "${aws_iam_user.hgbundler.arn}"

  providers = {
    aws = "aws.awsprovider-us-west-2"
  }
}

module "s3-eu1" {
  source = "./modules/s3"
  bundler_arn = "${aws_iam_user.hgbundler.arn}"

  providers = {
    aws = "aws.awsprovider-eu-central-1"
  }
}

# Configure a CI-only hgweb mirror environment in us-west-2
module "ci-only-west2" {
  source = "./modules/ci-only"

  cidr_block = "10.191.5.0/24"
  environment_users = [
    "${aws_iam_user.user-cosheehan.name}",
  ]
  metadata_bucket_name = "${aws_s3_bucket.metadata-bucket.bucket}"
  mirror_ami = "${var.centos7_amis["us-west-2"]}"

  providers = {
    aws = "aws.awsprovider-us-west-2"
  }
}
