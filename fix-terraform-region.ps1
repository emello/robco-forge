# RobCo Forge - Fix Terraform Region Mismatch (PowerShell)
# This script reinitializes Terraform after region configuration changes

param(
    [string]$Environment = "staging"
)

Write-Host "========================================" -ForegroundColor Blue
Write-Host "Fixing Terraform Region Configuration" -ForegroundColor Blue
Write-Host "========================================" -ForegroundColor Blue
Write-Host ""

Write-Host "Environment: $Environment" -ForegroundColor Blue
Write-Host ""

# Navigate to environment directory
Set-Location "terraform/environments/$Environment"

Write-Host "⚠ Removing old Terraform state..." -ForegroundColor Yellow
if (Test-Path ".terraform") {
    Remove-Item -Recurse -Force ".terraform"
}
if (Test-Path ".terraform.lock.hcl") {
    Remove-Item -Force ".terraform.lock.hcl"
}

Write-Host "✓ Old state removed" -ForegroundColor Green
Write-Host ""

Write-Host "ℹ Reinitializing Terraform with correct region (us-east-1)..." -ForegroundColor Blue
terraform init

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "Terraform Region Fix Complete!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "ℹ You can now run:" -ForegroundColor Blue
Write-Host "  terraform plan" -ForegroundColor Cyan
Write-Host "  terraform apply" -ForegroundColor Cyan
Write-Host ""
