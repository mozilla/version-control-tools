# This data source retrieves information about the
# aws provider for this module instance
data "aws_region" "provider-region" {}

resource "aws_s3_bucket" "moz-hg-logging" {
  bucket = "moz-hg-logging-${data.aws_region.provider-region.name}"
  acl = "log-delivery-write"
  
  tags {
      App = "hgmo"
      Env = "prod"
      Owner = "gps@mozilla.com"
      Bugid = "1510795"
      Name = "hg logging bucket in ${data.aws_region.provider-region.name}"
  }
}

# Per-region S3 buckets hold bundle objects. Each region should be
# identically configured except for the per-region differences.
resource "aws_s3_bucket" "hg_bundles" {
  # Buckets are pinned to a specific region and therefore have to use
  # an explicit provider for that region.
  bucket = "moz-hg-${data.aws_region.provider-region.name}"
  acl = "private"

  tags {
    App = "hgmo"
    Env = "prod"
    Owner = "gps@mozilla.com"
    Bugid = "1510795"
    Name = "hg bundles bucket in ${data.aws_region.provider-region.name}"
  }

  # Serve the auto-generated index when / is requested.
  website {
    index_document = "index.html"
  }

  # Send access logs to S3 so we can audit and monitor.
  logging {
    target_bucket = "moz-hg-logging-${data.aws_region.provider-region.name}"
    target_prefix = "s3/hg/"
  }

  # Objects automatically expire after 1 week.
  lifecycle_rule {
    enabled = true
    prefix = ""
    expiration {
      days = 7
    }
    noncurrent_version_expiration {
      days = 1
    }
  }
}

# Define the policy for bundle access
data "aws_iam_policy_document" "hg_bundles" {
  # Grant bundler user access to upload and modify objects.
  statement {
    effect = "Allow"
    actions = [
      "s3:DeleteObject",
      "s3:GetObject",
      "s3:PutObject",
    ]
    resources = [
      "${aws_s3_bucket.hg_bundles.arn}/*",
    ]
    principals {
      type = "AWS"
      identifiers = ["${var.bundler_arn}"]
    }
  }

  # Grant all access to read S3 objects.
  statement {
    effect = "Allow"
    actions = [
      "s3:ListBucket",
    ]
    resources = ["${aws_s3_bucket.hg_bundles.arn}"]
    principals {
      type = "AWS"
      identifiers = ["*"]
    }
  }

  statement {
    effect = "Allow"
    actions = [
      "s3:GetObjectTorrent",
      "s3:GetObject",
    ]
    resources = [
      "${aws_s3_bucket.hg_bundles.arn}/*",
    ]
    principals {
      type = "AWS"
      identifiers = ["*"]
    }
  }
}

resource "aws_s3_bucket_policy" "hg_bundles_policy" {
  bucket = "${aws_s3_bucket.hg_bundles.bucket}"
  policy = "${data.aws_iam_policy_document.hg_bundles.json}"
}
