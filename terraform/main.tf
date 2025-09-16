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
  tags          = {
    "AKIA2GHRPQZBOYHYVYMW" = "hgaws access key - Terraform"
  }
  tags_all      = {
    "AKIA2GHRPQZBOYHYVYMW" = "hgaws access key - Terraform"
  }
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

# Configure AWS VPC in us-west-2
module "vpc-uw2" {
  source = "./modules/aws-vpc"

  az_b_count           = 2
  backup_node          = 1
  cidr_block           = "10.191.5.0/24"
  metadata_bucket_name = aws_s3_bucket.metadata-bucket.bucket
  mirror_ami           = var.centos7_amis["us-west-2"]
  taskcluster_vpc_cidr = "10.144.0.0/16"

  providers = {
    aws = aws.awsprovider-us-west-2
  }
}

# Service account to upload the bundles
resource "google_service_account" "gcp-hgbundler" {
  account_id   = "hgbundler"
  display_name = "hgbundler"
  description  = "Upload Mercurial clonebundles to Google Cloud Storage buckets"
}

# GCP buckets for bundles
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

resource "google_storage_bucket_iam_member" "hgbundler-access-uc1" {
  bucket = google_storage_bucket.gcp-bundles-uc1.name
  role   = "roles/storage.objectAdmin"
  member = "serviceAccount:${google_service_account.gcp-hgbundler.email}"
}

# Allow public read access to the world for the bundles buckets
resource "google_storage_bucket_iam_member" "public-bundle-rule-uc1" {
  bucket = google_storage_bucket.gcp-bundles-uc1.name
  role   = "roles/storage.objectViewer"

  member = "allUsers"
}

resource "google_storage_bucket" "gcp-bundles-uw1" {
  name          = "moz-hg-bundles-gcp-us-west1"
  location      = "us-west1"
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

resource "google_storage_bucket_iam_member" "hgbundler-access-uw1" {
  bucket = google_storage_bucket.gcp-bundles-uw1.name
  role   = "roles/storage.objectAdmin"
  member = "serviceAccount:${google_service_account.gcp-hgbundler.email}"
}

resource "google_storage_bucket_iam_member" "public-bundle-rule-uw1" {
  bucket = google_storage_bucket.gcp-bundles-uw1.name
  role   = "roles/storage.objectViewer"

  member = "allUsers"
}

resource "google_storage_bucket" "gcp-bundles-na-ne1" {
  name          = "moz-hg-bundles-gcp-na-ne1"
  location      = "northamerica-northeast1"
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

resource "google_storage_bucket_iam_member" "hgbundler-access-na-ne1" {
  bucket = google_storage_bucket.gcp-bundles-na-ne1.name
  role   = "roles/storage.objectAdmin"
  member = "serviceAccount:${google_service_account.gcp-hgbundler.email}"
}

resource "google_storage_bucket_iam_member" "public-bundle-rule-na-ne1" {
  bucket = google_storage_bucket.gcp-bundles-na-ne1.name
  role   = "roles/storage.objectViewer"

  member = "allUsers"
}

resource "google_storage_bucket" "gcp-bundles-us-east1" {
  name          = "moz-hg-bundles-gcp-us-east1"
  location      = "us-east1"
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

resource "google_storage_bucket_iam_member" "hgbundler-access-us-east1" {
  bucket = google_storage_bucket.gcp-bundles-us-east1.name
  role   = "roles/storage.objectAdmin"
  member = "serviceAccount:${google_service_account.gcp-hgbundler.email}"
}

resource "google_storage_bucket_iam_member" "public-bundle-rule-us-east1" {
  bucket = google_storage_bucket.gcp-bundles-us-east1.name
  role   = "roles/storage.objectViewer"

  member = "allUsers"
}
