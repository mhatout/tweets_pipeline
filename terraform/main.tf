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
  # uniform_bucket_level_access = true

  versioning {
    enabled     = true
  }

  lifecycle_rule {
    action {
      type = "Delete"
    }
    condition {
      age = 60  // days
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
    }
    node_config {
      # machine_type = "n1-standard-1"
      # network    = google_compute_network.composer-network.id
      # subnetwork = google_compute_subnetwork.composer-subnetwork.id
      service_account = google_service_account.composer_service_account.name	
    }
    # database_config {
    #   machine_type = "db-n1-standard-2"
    # }

    # web_server_config {
    #   machine_type = "composer-n1-webserver-2"
    # }
  }
}

# resource "google_compute_network" "composer-network" {
#   name                    = "composer-network"
#   auto_create_subnetworks = false
# }

# resource "google_compute_subnetwork" "composer-subnetwork" {
#   name          = "composer-subnetwork"
#   ip_cidr_range = "10.2.0.0/24"
#   region        = var.region
#   network       = google_compute_network.composer-network.id
# }

resource "google_service_account" "composer_service_account" {
  account_id   = "composer-env-account"
  display_name = "Composer Environment Service Account"
}

resource "google_project_iam_member" "composer-worker" {
  project = var.project
  # for_each = toset([
  #   "roles/resourcemanager.projectIamAdmin",
  #   "roles/owner",
  #   "roles/composer.admin",
  #   "roles/composer.ServiceAgentV2Ext",
  # ])
  # role    = each.key
  role   = "roles/composer.worker"
  member  = "serviceAccount:${google_service_account.composer_service_account.email}"
}

# resource "google_project_iam_policy" "composer-worker" {
#   project = var.project
#   policy_data = data.google_iam_policy.composer2.policy_data
# }

# data "google_iam_policy" "composer2" {

#   # IMPORTANT: Include all other IAM bindings for your project.
#   # Existing IAM policy in your project is overwritten with parameters
#   # specified here.

#   binding {
#     role = "roles/composer.ServiceAgentV2Ext"

#     members = [
#       "serviceAccount:service-476527518525@cloudcomposer-accounts.iam.gserviceaccount.com",
#     ]
#   }

#   binding {
#     role = "roles/composer.admin"

#     members = [
#       "serviceAccount:service-476527518525@cloudcomposer-accounts.iam.gserviceaccount.com",
#     ]
#   }

#   # Edit the section below along with the example binding to match your
#   # project's IAM policy.
#   binding {
#     role = "roles/owner"
#     members = ["serviceAccount:service-476527518525@cloudcomposer-accounts.iam.gserviceaccount.com"]
#   }
# }