
variable "frontend_image" {
  description = "Docker image of the frontend"
  type        = string
}

variable "laptop_a_ip" {
  description = "IP address of Student A's laptop"
  type        = string
}

variable "replicas" {
  description = "Number of frontend replicas"
  type        = number
  default     = 2
}
