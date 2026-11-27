resource "kubernetes_deployment" "frontend-deployment" {
  metadata {
    name = "frontend-deployment"

    labels = {
      app = "frontend"
    }
  }

  spec {
    replicas = var.replicas

    selector {
      match_labels = {
        app = "frontend"
      }
    }

    template {
      metadata {
        labels = {
          app = "frontend"
        }
      }

      spec {
        container {
          name  = "frontend"
          image = var.frontend_image

          port {
            container_port = 80
          }

          env {
            name  = "VITE_API_BASE_URL"
            value = var.api_base_url
          }

          security_context {
            run_as_non_root = true
            run_as_user     = 1000
          }

          resources {
            limits = {
              cpu    = "500m"
              memory = "512Mi"
            }

            requests = {
              cpu    = "100m"
              memory = "128Mi"
            }
          }
        }
      }
    }
  }
}

resource "kubernetes_service" "frontend-service" {
  metadata {
    name = "frontend-service"
  }

  spec {
    selector = {
      app = "frontend"
    }

    port {
      port        = 80
      target_port = 80
    }

    type = "LoadBalancer"
  }
}