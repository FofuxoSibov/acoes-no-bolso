output "public_ip" {
  description = "IP Público da instância EC2"
  value       = module.app_server.public_ip
}

output "app_url" {
  description = "URL para acessar a aplicação"
  value       = "http://${module.app_server.public_ip}"
}

