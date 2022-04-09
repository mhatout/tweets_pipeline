terraform {
  required_version = ">= 1.0"
  backend "local" {}  # Can change from "local" to "gcs" (for google) or "s3" (for aws), if you would like to preserve your tf-state online
  required_providers {
    google = {
      source  = "hashicorp/google"
    }
  }
}

provider "google" {
  project = var.project
  region = var.region
  // credentials = file(var.credentials)  # Use this if you do not want to set env-var GOOGLE_APPLICATION_CREDENTIALS
}

# Data Lake Bucket
# Ref: https://registry.terraform.io/providers/hashicorp/google/latest/docs/resources/storage_bucket
resource "google_storage_bucket" "data-lake-bucket" {
  name = "${local.data_lake_bucket}_${var.project}" # Concatenating DL bucket & Project name for unique naming
  location = var.region

  # Optional, but recommended settings:
  storage_class = var.storage_class

  versioning {
    enabled     = true
  }

  lifecycle_rule {
    action {
      type = "Delete"
    }
    condition {
      age = 90  // days
    }
  }

  force_destroy = true
}

# DWH
# Ref: https://registry.terraform.io/providers/hashicorp/google/latest/docs/resources/bigquery_dataset
resource "google_bigquery_dataset" "dataset" {
  dataset_id = var.BQ_DATASET
}

# Google Cloud Composer (Airflow cluster)
# Ref: https://registry.terraform.io/providers/hashicorp/google/latest/docs/resources/composer_environment
resource "google_composer_environment" "airflow" {
  name   = "airflow"
  region = var.region
  config {
    node_count = 4
    software_config {
      image_version = "composer-1.18.3-airflow-2.2.3"
      env_variables = {
        project = var.project
        region = var.dataproc_region
        bq_dataset = var.BQ_DATASET
        gs_bucket = "${local.data_lake_bucket}_${var.project}"
        data_source=var.data_source
      }
    }
    node_config {
      service_account = google_service_account.composer_service_account.name	
    }
  }
}

resource "google_service_account" "composer_service_account" {
  account_id   = "composer-env-account"
  display_name = "Composer Environment Service Account"
}

resource "google_project_iam_member" "composer-worker" {
  project = var.project
  for_each = toset([
    "roles/composer.worker",
    "roles/dataproc.admin",
    "roles/iam.serviceAccountUser",
    "roles/bigquery.admin",
  ])
  role    = each.key
  member  = "serviceAccount:${google_service_account.composer_service_account.email}"
}