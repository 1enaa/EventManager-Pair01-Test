
output "frontend_deployment_name" {
  value = kubernetes_deployment.frontend.metadata[0].name
}

output "frontend_service_name" {
  value = kubernetes_service.frontend.metadata[0].name
}

output "frontend_service_type" {
  value = kubernetes_service.frontend.spec[0].type
}

output "frontend_api_url" {
  value = "http://${var.laptop_a_ip}:8000"
}
