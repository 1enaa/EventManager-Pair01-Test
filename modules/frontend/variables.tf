variable "frontend_image" {
  description = "Docker image of the frontend"
  type        = string
}

variable "api_base_url" {
  description = "Backend URL of Laptop A (tunnel URL, no trailing slash)"
  type        = string
}

variable "replicas" {
  description = "Number of frontend replicas"
  type        = number
  default     = 2
}