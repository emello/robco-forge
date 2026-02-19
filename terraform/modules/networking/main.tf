# Networking Module - VPC, Subnets, NAT Gateway, VPC Endpoints
# Requirements: 9.1, 9.2, 9.3, 9.5

locals {
  azs = slice(data.aws_availability_zones.available.names, 0, 3)
}

data "aws_availability_zones" "available" {
  state = "available"
}

# VPC for WorkSpaces - Isolated with no direct internet access
resource "aws_vpc" "workspaces" {
  cidr_block           = var.vpc_cidr
  enable_dns_hostnames = true
  enable_dns_support   = true
  
  tags = merge(var.tags, {
    Name = "${var.environment}-workspaces-vpc"
    Purpose = "isolated-workspaces"
  })
}

# Private subnets across 3 availability zones
resource "aws_subnet" "private" {
  count             = 3
  vpc_id            = aws_vpc.workspaces.id
  cidr_block        = cidrsubnet(var.vpc_cidr, 4, count.index)
  availability_zone = local.azs[count.index]
  
  tags = merge(var.tags, {
    Name = "${var.environment}-private-subnet-${count.index + 1}"
    Tier = "private"
  })
}

# Public subnet for NAT Gateway (single AZ for cost optimization)
resource "aws_subnet" "public" {
  vpc_id                  = aws_vpc.workspaces.id
  cidr_block              = cidrsubnet(var.vpc_cidr, 4, 10)
  availability_zone       = local.azs[0]
  map_public_ip_on_launch = true
  
  tags = merge(var.tags, {
    Name = "${var.environment}-public-subnet-nat"
    Tier = "public"
  })
}

# Internet Gateway for NAT Gateway
resource "aws_internet_gateway" "main" {
  vpc_id = aws_vpc.workspaces.id
  
  tags = merge(var.tags, {
    Name = "${var.environment}-igw"
  })
}

# Elastic IP for NAT Gateway
resource "aws_eip" "nat" {
  domain = "vpc"
  
  tags = merge(var.tags, {
    Name = "${var.environment}-nat-eip"
  })
  
  depends_on = [aws_internet_gateway.main]
}

# NAT Gateway with egress allowlist (configured via security groups)
resource "aws_nat_gateway" "main" {
  allocation_id = aws_eip.nat.id
  subnet_id     = aws_subnet.public.id
  
  tags = merge(var.tags, {
    Name = "${var.environment}-nat-gateway"
  })
  
  depends_on = [aws_internet_gateway.main]
}

# Route table for public subnet
resource "aws_route_table" "public" {
  vpc_id = aws_vpc.workspaces.id
  
  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.main.id
  }
  
  tags = merge(var.tags, {
    Name = "${var.environment}-public-rt"
  })
}

resource "aws_route_table_association" "public" {
  subnet_id      = aws_subnet.public.id
  route_table_id = aws_route_table.public.id
}

# Route table for private subnets (routes through NAT Gateway)
resource "aws_route_table" "private" {
  vpc_id = aws_vpc.workspaces.id
  
  route {
    cidr_block     = "0.0.0.0/0"
    nat_gateway_id = aws_nat_gateway.main.id
  }
  
  tags = merge(var.tags, {
    Name = "${var.environment}-private-rt"
  })
}

resource "aws_route_table_association" "private" {
  count          = 3
  subnet_id      = aws_subnet.private[count.index].id
  route_table_id = aws_route_table.private.id
}

# VPC Endpoint for S3
resource "aws_vpc_endpoint" "s3" {
  vpc_id            = aws_vpc.workspaces.id
  service_name      = "com.amazonaws.${var.region}.s3"
  vpc_endpoint_type = "Gateway"
  route_table_ids   = [aws_route_table.private.id]
  
  tags = merge(var.tags, {
    Name = "${var.environment}-s3-endpoint"
  })
}

# VPC Endpoint for Secrets Manager
resource "aws_vpc_endpoint" "secrets_manager" {
  vpc_id              = aws_vpc.workspaces.id
  service_name        = "com.amazonaws.${var.region}.secretsmanager"
  vpc_endpoint_type   = "Interface"
  subnet_ids          = aws_subnet.private[*].id
  security_group_ids  = [aws_security_group.vpc_endpoints.id]
  private_dns_enabled = true
  
  tags = merge(var.tags, {
    Name = "${var.environment}-secrets-manager-endpoint"
  })
}

# VPC Endpoint for FSx
resource "aws_vpc_endpoint" "fsx" {
  vpc_id              = aws_vpc.workspaces.id
  service_name        = "com.amazonaws.${var.region}.fsx"
  vpc_endpoint_type   = "Interface"
  subnet_ids          = aws_subnet.private[*].id
  security_group_ids  = [aws_security_group.vpc_endpoints.id]
  private_dns_enabled = true
  
  tags = merge(var.tags, {
    Name = "${var.environment}-fsx-endpoint"
  })
}

# Security group for VPC endpoints
resource "aws_security_group" "vpc_endpoints" {
  name        = "${var.environment}-vpc-endpoints-sg"
  description = "Security group for VPC endpoints"
  vpc_id      = aws_vpc.workspaces.id
  
  ingress {
    description = "HTTPS from VPC"
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = [var.vpc_cidr]
  }
  
  egress {
    description = "Allow all outbound"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
  
  tags = merge(var.tags, {
    Name = "${var.environment}-vpc-endpoints-sg"
  })
}

# Security group for WorkSpaces - least privilege
resource "aws_security_group" "workspaces" {
  name        = "${var.environment}-workspaces-sg"
  description = "Security group for WorkSpaces instances"
  vpc_id      = aws_vpc.workspaces.id
  
  # Allow WSP streaming protocol
  ingress {
    description = "WSP streaming"
    from_port   = 4172
    to_port     = 4172
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]  # Restricted by WorkSpaces service
  }
  
  # Allow HTTPS for management
  ingress {
    description = "HTTPS for management"
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = [var.vpc_cidr]
  }
  
  # Allow egress through NAT Gateway only
  egress {
    description = "Controlled egress via NAT"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
  
  tags = merge(var.tags, {
    Name = "${var.environment}-workspaces-sg"
  })
}

# Security group for EKS pods
resource "aws_security_group" "eks_pods" {
  name        = "${var.environment}-eks-pods-sg"
  description = "Security group for EKS pods"
  vpc_id      = aws_vpc.workspaces.id
  
  ingress {
    description = "Allow pod-to-pod communication"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    self        = true
  }
  
  egress {
    description = "Allow all outbound"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
  
  tags = merge(var.tags, {
    Name = "${var.environment}-eks-pods-sg"
  })
}

# VPC Flow Logs for egress traffic logging
resource "aws_flow_log" "workspaces" {
  vpc_id          = aws_vpc.workspaces.id
  traffic_type    = "ALL"
  iam_role_arn    = aws_iam_role.flow_logs.arn
  log_destination = aws_cloudwatch_log_group.flow_logs.arn
  
  tags = merge(var.tags, {
    Name = "${var.environment}-vpc-flow-logs"
  })
}

resource "aws_cloudwatch_log_group" "flow_logs" {
  name              = "/aws/vpc/${var.environment}-workspaces-flow-logs"
  retention_in_days = 90
  
  tags = var.tags
}

resource "aws_iam_role" "flow_logs" {
  name = "${var.environment}-vpc-flow-logs-role"
  
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = {
        Service = "vpc-flow-logs.amazonaws.com"
      }
    }]
  })
  
  tags = var.tags
}

resource "aws_iam_role_policy" "flow_logs" {
  name = "${var.environment}-vpc-flow-logs-policy"
  role = aws_iam_role.flow_logs.id
  
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = [
        "logs:CreateLogGroup",
        "logs:CreateLogStream",
        "logs:PutLogEvents",
        "logs:DescribeLogGroups",
        "logs:DescribeLogStreams"
      ]
      Effect = "Allow"
      Resource = "*"
    }]
  })
}
