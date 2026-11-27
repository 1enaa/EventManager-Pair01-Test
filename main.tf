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
  laptop_a_ip    = var.laptop_a_ip
}
