
output "backend_service_name" {
  description = "Name of the backend Kubernetes service"
  value       = kubernetes_service.backend-service.metadata[0].name
}

output "backend_service_port" {
  description = "Backend service port"
  value       = kubernetes_service.backend-service.spec[0].port[0].port
}

output "backend_deployment_name" {
  description = "Backend Kubernetes deployment name"
  value       = kubernetes_deployment.backend-deployment.metadata[0].name
}

output "sqlite_pvc_name" {
  description = "SQLite persistent volume claim name"
  value       = kubernetes_persistent_volume_claim.sqlite-pvc.metadata[0].name
}
