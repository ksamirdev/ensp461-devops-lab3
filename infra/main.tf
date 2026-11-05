terraform {
  required_version = ">= 1.9"
  required_providers {
    docker = {
      source  = "kreuzwerker/docker"
      version = "~> 3.6"
    }
  }
}

provider "docker" {}

variable "replicas" {
  description = "Number of text-stats containers"
  type        = number
  default     = 2

  validation {
    condition     = var.replicas >= 1 && var.replicas <= 10
    error_message = "replicas must be between 1 and 10 (ports 8310-8319 are reserved)."
  }
}

variable "release" {
  description = "Release reported by the service"
  type        = string
  default     = "3.0.0"
}

resource "docker_network" "lab" {
  name = "lab3-tf"
}

# Built beforehand with `docker build`; Terraform only provisions from it
data "docker_image" "text_stats" {
  name = "text-stats:${var.release}"
}

resource "docker_container" "text_stats" {
  count = var.replicas
  name  = "text-stats-${count.index + 1}"
  image = data.docker_image.text_stats.id
  env   = ["RELEASE=${var.release}"]

  networks_advanced {
    name = docker_network.lab.name
  }
  ports {
    internal = 5000
    external = 8310 + count.index
    ip       = "127.0.0.1"
  }
  restart = "unless-stopped"

  # The Docker daemon injects default log options; without this every plan replaces the containers
  lifecycle {
    ignore_changes = [log_opts]
  }
}

output "urls" {
  value = [for c in docker_container.text_stats : "http://localhost:${c.ports[0].external}"]
}
