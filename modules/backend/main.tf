
# -----------------------------------------
# 1. SQLite PersistentVolumeClaim
# -----------------------------------------

resource "kubernetes_persistent_volume_claim" "sqlite-pvc" {
  wait_until_bound = false

  metadata {
    name      = "sqlite-pvc"
    namespace = var.namespace
  }

  spec {
    access_modes = ["ReadWriteOnce"]

    resources {
      requests = {
        storage = var.storage_size
      }
    }
  }
}

# -----------------------------------------
# 2. Backend Deployment
# -----------------------------------------

resource "kubernetes_deployment" "backend-deployment" {
  metadata {
    name      = "backend-deployment"
    namespace = var.namespace

    labels = {
      app = "backend"
    }
  }

  spec {
    replicas = var.replicas

    selector {
      match_labels = {
        app = "backend"
      }
    }

    template {
      metadata {
        labels = {
          app = "backend"
        }
      }

      spec {
        security_context {
          run_as_user     = 1000
          run_as_non_root = true
          fs_group        = 1000
        }

        container {
          name  = "backend"
          image = var.backend_image

          port {
            container_port = var.container_port
          }

          env {
            name  = "DATABASE_URL"
            value = "sqlite:////app/data/events.db"
          }

          liveness_probe {
            http_get {
              path = "/events/"
              port = var.container_port
            }

            initial_delay_seconds = 5
            period_seconds        = 10
          }

          readiness_probe {
            http_get {
              path = "/events/"
              port = var.container_port
            }

            initial_delay_seconds = 3
            period_seconds        = 5
          }

          resources {
            limits = {
              cpu    = "500m"
              memory = "512Mi"
            }
          }

          volume_mount {
            name       = "sqlite-storage"
            mount_path = "/app/data"
          }
        }

        volume {
          name = "sqlite-storage"

          persistent_volume_claim {
            claim_name = kubernetes_persistent_volume_claim.sqlite-pvc.metadata[0].name
          }
        }
      }
    }
  }
}

# -----------------------------------------
# 3. Backend ClusterIP Service
# -----------------------------------------

resource "kubernetes_service" "backend-service" {
  metadata {
    name      = "backend-service"
    namespace = var.namespace
  }

  spec {
    type = "ClusterIP"

    selector = {
      app = "backend"
    }

    port {
      port        = 8000
      target_port = 8000
      protocol    = "TCP"
    }
  }
}
