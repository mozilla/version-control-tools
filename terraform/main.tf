# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

# Configure the S3 remote state backend
terraform {
  required_version = ">= 0.11.0"

  backend "s3" {
    acl     = "private"
    bucket  = "hgaws-metadata"
    encrypt = true
    key     = "tfstate/terraform.tfstate"
    profile = "hgaws"
    region  = "us-west-2"
  }
}

data "terraform_remote_state" "remotestate" {
  backend = "s3"

  config = {
    acl     = "private"
    bucket  = "hgaws-metadata"
    key     = "tfstate/terraform.tfstate"
    profile = "hgaws"
    region  = "us-west-2"
  }
}

# An annoying technicality where we need to declare the
# default provider, otherwise we will be prompted when
# running `terraform apply`. See link for more info
# https://github.com/terraform-providers/terraform-provider-aws/issues/1043
provider "aws" {
  region  = "us-west-2"
  profile = "hgaws"
}

# Configure the "AWS" providers.
# Credentials for the AWS account should be set in the
# ~/.aws/credentials file, in the `hgaws` profile
provider "aws" {
  alias   = "awsprovider-us-west-1"
  region  = "us-west-1"
  profile = "hgaws"
}

provider "aws" {
  alias   = "awsprovider-us-west-2"
  region  = "us-west-2"
  profile = "hgaws"
}

provider "aws" {
  alias   = "awsprovider-us-east-1"
  region  = "us-east-1"
  profile = "hgaws"
}

provider "aws" {
  alias   = "awsprovider-us-east-2"
  region  = "us-east-2"
  profile = "hgaws"
}

provider "aws" {
  alias   = "awsprovider-eu-central-1"
  region  = "eu-central-1"
  profile = "hgaws"
}

provider "google" {
  project = "hgmo-236019"
  region  = "us-central1"
}

# Configure a bucket to hold various metadata (remote state, etc)
resource "aws_s3_bucket" "metadata-bucket" {
  bucket = "hgaws-metadata"
  acl    = "private"

  versioning {
    enabled = true
  }

  tags = {
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
        aws_iam_user.user-cosheehan.arn,
      ]
    }
    effect = "Allow"
    actions = [
      "s3:ListBucket",
    ]
    resources = [
      aws_s3_bucket.metadata-bucket.arn,
    ]
  }

  statement {
    principals {
      type = "AWS"
      identifiers = [
        aws_iam_user.user-cosheehan.arn,
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
  provider = aws.awsprovider-us-west-2
  bucket   = aws_s3_bucket.metadata-bucket.bucket
  policy   = data.aws_iam_policy_document.metadata-bucket-policy-definition.json
}

# Configure S3 buckets for bundles and caching
module "s3-east1" {
  source      = "./modules/s3"
  bundler_arn = aws_iam_user.hgbundler.arn

  providers = {
    aws = aws.awsprovider-us-east-1
  }
}

module "s3-east2" {
  source      = "./modules/s3"
  bundler_arn = aws_iam_user.hgbundler.arn

  providers = {
    aws = aws.awsprovider-us-east-2
  }
}

module "s3-west1" {
  source      = "./modules/s3"
  bundler_arn = aws_iam_user.hgbundler.arn

  providers = {
    aws = aws.awsprovider-us-west-1
  }
}

module "s3-west2" {
  source      = "./modules/s3"
  bundler_arn = aws_iam_user.hgbundler.arn

  providers = {
    aws = aws.awsprovider-us-west-2
  }
}

module "s3-eu1" {
  source      = "./modules/s3"
  bundler_arn = aws_iam_user.hgbundler.arn

  providers = {
    aws = aws.awsprovider-eu-central-1
  }
}

resource "aws_route53_zone" "hgzone" {
  name    = "hgmointernal.net"
  comment = "hg internal public hosted zone"

  tags = {
    Name = "hgmo internal public hosted zone"
  }
}

# Configure AWS VPC in us-west-2
module "vpc-uw2" {
  source = "./modules/aws-vpc"

  cidr_block           = "10.191.5.0/24"
  metadata_bucket_name = aws_s3_bucket.metadata-bucket.bucket
  mirror_ami           = var.centos7_amis["us-west-2"]
  route53_zone_id      = aws_route53_zone.hgzone.id
  taskcluster_vpc_cidr = "10.144.0.0/16"

  providers = {
    aws = aws.awsprovider-us-west-2
  }
}

# Configure AWS VPC in us-west-1
module "vpc-uw1" {
  source = "./modules/aws-vpc"

  cidr_block           = "10.191.11.0/24"
  metadata_bucket_name = aws_s3_bucket.metadata-bucket.bucket
  mirror_ami           = var.centos7_amis["us-west-1"]
  route53_zone_id      = aws_route53_zone.hgzone.id
  taskcluster_vpc_cidr = "10.143.0.0/16"

  providers = {
    aws = aws.awsprovider-us-west-1
  }
}

# Configure AWS VPC in us-east-1
module "vpc-ue1" {
  source = "./modules/aws-vpc"

  cidr_block           = "10.191.12.0/24"
  metadata_bucket_name = aws_s3_bucket.metadata-bucket.bucket
  mirror_ami           = var.centos7_amis["us-east-1"]
  route53_zone_id      = aws_route53_zone.hgzone.id
  taskcluster_vpc_cidr = "10.145.0.0/16"

  providers = {
    aws = aws.awsprovider-us-east-1
  }
}

# Service account to upload the bundles
resource "google_service_account" "gcp-hgbundler" {
  account_id   = "hgbundler"
  display_name = "hgbundler"
}

resource "google_service_account_key" "gcp-hgbundler-key" {
  service_account_id = google_service_account.gcp-hgbundler.id
  public_key_type    = "TYPE_X509_PEM_FILE"
}

# Bucket for bundles
resource "google_storage_bucket" "gcp-bundles-uc1" {
  name          = "moz-hg-bundles-gcp-us-central1"
  location      = "us-central1"
  storage_class = "STANDARD"

  # Delete after 1 week inactive
  lifecycle_rule {
    action {
      type = "Delete"
    }
    condition {
      age        = 7
      with_state = "ANY"
    }
  }

  # Ensure bundles are around for 1 week minimum
  retention_policy {
    is_locked        = false
    retention_period = 604800
  }
}

resource "google_storage_bucket_iam_member" "hgbundler-access" {
  bucket = google_storage_bucket.gcp-bundles-uc1.name
  role   = "roles/storage.objectAdmin"
  member = google_service_account.gcp-hgbundler.name
}

# Allow public read access to the world for the bundles bucket
resource "google_storage_bucket_iam_member" "public-bundle-rule" {
  bucket = google_storage_bucket.gcp-bundles-uc1.name
  role   = "roles/storage.objectViewer"

  member = "allUsers"
}
