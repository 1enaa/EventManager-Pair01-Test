
variable "namespace" {
  description = "Kubernetes namespace for the backend"
  type        = string
  default     = "default"
}

variable "backend_image" {
  description = "Docker image used by the backend"
  type        = string
  default     = "linasahour/eventmanager-backend:latest"
}

variable "replicas" {
  description = "Number of backend replicas"
  type        = number
  default     = 2
}

variable "storage_size" {
  description = "Persistent storage requested by SQLite"
  type        = string
  default     = "1Gi"
}

variable "container_port" {
  description = "Backend application port"
  type        = number
  default     = 8000
}
