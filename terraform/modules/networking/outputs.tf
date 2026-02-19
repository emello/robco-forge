# Outputs for networking module

output "vpc_id" {
  description = "ID of the VPC"
  value       = aws_vpc.workspaces.id
}

output "vpc_cidr" {
  description = "CIDR block of the VPC"
  value       = aws_vpc.workspaces.cidr_block
}

output "private_subnet_ids" {
  description = "IDs of private subnets"
  value       = aws_subnet.private[*].id
}

output "public_subnet_id" {
  description = "ID of public subnet"
  value       = aws_subnet.public.id
}

output "nat_gateway_id" {
  description = "ID of NAT Gateway"
  value       = aws_nat_gateway.main.id
}

output "workspaces_security_group_id" {
  description = "Security group ID for WorkSpaces"
  value       = aws_security_group.workspaces.id
}

output "eks_pods_security_group_id" {
  description = "Security group ID for EKS pods"
  value       = aws_security_group.eks_pods.id
}

output "vpc_endpoints_security_group_id" {
  description = "Security group ID for VPC endpoints"
  value       = aws_security_group.vpc_endpoints.id
}

output "availability_zones" {
  description = "Availability zones used"
  value       = local.azs
}
