terraform {
  required_providers {
    kubernetes = {
      source  = "hashicorp/kubernetes"
      version = "~> 2.20"
    }
  }
}

provider "kubernetes" {
  config_path    = "~/.kube/config"
  config_context = "docker-desktop"
}

module "backend" {
  source = "./modules/backend"
}
module "frontend" {
  source = "./modules/frontend"

  frontend_image = "${var.docker_username}/eventmanager-frontend:latest"
  api_base_url   = var.api_base_url
}
