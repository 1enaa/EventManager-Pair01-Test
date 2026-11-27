output "frontend_deployment_name" {
  value = kubernetes_deployment.frontend-deployment.metadata[0].name
}

output "frontend_service_name" {
  value = kubernetes_service.frontend-service.metadata[0].name
}

output "frontend_service_type" {
  value = kubernetes_service.frontend-service.spec[0].type
}

output "frontend_api_url" {
  value = var.api_base_url
}