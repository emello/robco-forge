# Git & GitHub Setup Guide for RobCo Forge

## Quick Start (5 Minutes)

### 1. Initialize Git Repository

```bash
# Navigate to your project root
cd /path/to/robco-forge

# Initialize git
git init

# Add all files
git add .

# Create initial commit
git commit -m "Initial commit: RobCo Forge platform v1.0.0"
```

### 2. Create GitHub Repository

**Option A: Via GitHub Website**
1. Go to https://github.com/new
2. Repository name: `robco-forge`
3. Description: "Self-service cloud engineering workstation platform"
4. Choose Private (recommended for production code)
5. **DO NOT** initialize with README, .gitignore, or license
6. Click "Create repository"

**Option B: Via GitHub CLI**
```bash
# Install GitHub CLI first: https://cli.github.com/
gh repo create robco-forge --private --source=. --remote=origin
```

### 3. Connect Local to GitHub

```bash
# Add GitHub as remote (replace YOUR-USERNAME)
git remote add origin https://github.com/YOUR-USERNAME/robco-forge.git

# Or use SSH (recommended)
git remote add origin git@github.com:YOUR-USERNAME/robco-forge.git

# Push to GitHub
git branch -M main
git push -u origin main
```

---

## Complete Setup Guide

### Step 1: Prepare Your Repository

#### A. Review What Will Be Committed

```bash
# See what files will be added
git status

# Review the .gitignore file
cat .gitignore
```

#### B. Important: Protect Secrets

The `.gitignore` file I created excludes:
- ✅ `*.tfvars` (contains passwords and secrets)
- ✅ `.env` files (API keys)
- ✅ `.terraform/` (Terraform state)
- ✅ `node_modules/` (dependencies)
- ✅ `__pycache__/` (Python cache)

**⚠️ CRITICAL**: Never commit:
- Passwords
- API keys
- AWS credentials
- Private keys
- Database connection strings

#### C. Create Example Files (Safe to Commit)

```bash
# Create example tfvars (without real secrets)
cp terraform/environments/staging/terraform.tfvars terraform/environments/staging/terraform.tfvars.example

# Edit the example file to remove real values
# Replace passwords with "CHANGE_ME"
# Replace IPs with "x.x.x.x"
```

### Step 2: Initial Commit

```bash
# Stage all files
git add .

# Review what's being committed
git status

# Create initial commit
git commit -m "Initial commit: RobCo Forge platform

- Complete infrastructure (Terraform + CDK)
- API services (FastAPI)
- Lucy AI service
- Cost engine
- CLI tool
- Web portal (Next.js)
- Complete documentation
- Deployment scripts"

# Tag the release
git tag -a v1.0.0 -m "Version 1.0.0 - Production ready"
```

### Step 3: Create GitHub Repository

#### Option 1: GitHub Website

1. **Go to**: https://github.com/new
2. **Repository name**: `robco-forge`
3. **Description**: "Self-service cloud engineering workstation platform built on AWS WorkSpaces"
4. **Visibility**: 
   - **Private** (recommended) - Only you and collaborators can see
   - **Public** - Anyone can see (not recommended for production)
5. **Initialize**: Leave all checkboxes UNCHECKED
6. **Click**: "Create repository"

#### Option 2: GitHub CLI

```bash
# Install GitHub CLI
# Mac: brew install gh
# Windows: winget install GitHub.cli
# Linux: See https://cli.github.com/

# Login to GitHub
gh auth login

# Create private repository
gh repo create robco-forge \
  --private \
  --source=. \
  --remote=origin \
  --description="Self-service cloud engineering workstation platform"

# Push code
git push -u origin main
```

### Step 4: Connect and Push

```bash
# Add GitHub as remote
git remote add origin https://github.com/YOUR-USERNAME/robco-forge.git

# Verify remote
git remote -v

# Push code and tags
git push -u origin main
git push --tags
```

---

## Using Git in Your Workflow

### Daily Workflow

```bash
# 1. Pull latest changes
git pull origin main

# 2. Make changes to files
# ... edit files ...

# 3. Check what changed
git status
git diff

# 4. Stage changes
git add .
# Or stage specific files
git add terraform/modules/fsx/main.tf

# 5. Commit changes
git commit -m "Fix: Update FSx module to use WorkSpaces DNS IPs"

# 6. Push to GitHub
git push origin main
```

### Branch Strategy (Recommended)

```bash
# Create feature branch
git checkout -b feature/add-slack-integration

# Make changes
# ... edit files ...

# Commit changes
git add .
git commit -m "Add Slack integration for Lucy AI"

# Push branch to GitHub
git push -u origin feature/add-slack-integration

# Create Pull Request on GitHub
# After review and approval, merge to main
```

### Common Git Commands

```bash
# View commit history
git log --oneline

# View changes
git diff

# Undo changes (before commit)
git checkout -- filename.tf

# Undo last commit (keep changes)
git reset --soft HEAD~1

# View branches
git branch -a

# Switch branches
git checkout main

# Pull latest changes
git pull

# Push changes
git push

# View remote repositories
git remote -v
```

---

## Deployment Environment Setup

### Option 1: Clone to Deployment Server

```bash
# On your deployment server
git clone https://github.com/YOUR-USERNAME/robco-forge.git
cd robco-forge

# Create terraform.tfvars with real secrets
cp terraform/environments/staging/terraform.tfvars.example terraform/environments/staging/terraform.tfvars
nano terraform/environments/staging/terraform.tfvars
# Add real passwords and secrets

# Deploy
cd terraform/environments/staging
terraform init
terraform apply
```

### Option 2: Use GitHub Actions for CI/CD

Create `.github/workflows/deploy.yml`:

```yaml
name: Deploy to Staging

on:
  push:
    branches: [ main ]
  workflow_dispatch:

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Configure AWS Credentials
        uses: aws-actions/configure-aws-credentials@v2
        with:
          aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
          aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          aws-region: us-east-1
      
      - name: Setup Terraform
        uses: hashicorp/setup-terraform@v2
        with:
          terraform_version: 1.5.0
      
      - name: Terraform Init
        run: |
          cd terraform/environments/staging
          terraform init
      
      - name: Terraform Plan
        run: |
          cd terraform/environments/staging
          terraform plan
      
      - name: Terraform Apply
        if: github.ref == 'refs/heads/main'
        run: |
          cd terraform/environments/staging
          terraform apply -auto-approve
```

### Option 3: Pull Updates on Deployment Server

```bash
# On deployment server, pull latest changes
cd /path/to/robco-forge
git pull origin main

# Apply changes
cd terraform/environments/staging
terraform plan
terraform apply
```

---

## Managing Secrets Securely

### Never Commit These Files:
- ❌ `terraform.tfvars` (contains real secrets)
- ❌ `.env` files
- ❌ `*.pem` files
- ❌ AWS credentials

### Instead, Use:

#### 1. Environment Variables
```bash
export TF_VAR_directory_password="YourSecretPassword"
terraform apply
```

#### 2. AWS Secrets Manager
```bash
# Store secrets
aws secretsmanager create-secret \
  --name robco-forge/staging/directory-password \
  --secret-string "YourSecretPassword"

# Retrieve in Terraform
data "aws_secretsmanager_secret_version" "directory_password" {
  secret_id = "robco-forge/staging/directory-password"
}
```

#### 3. GitHub Secrets (for CI/CD)
1. Go to: Repository → Settings → Secrets and variables → Actions
2. Add secrets:
   - `AWS_ACCESS_KEY_ID`
   - `AWS_SECRET_ACCESS_KEY`
   - `TF_VAR_directory_password`

---

## Collaboration Workflow

### Adding Team Members

```bash
# On GitHub:
# Repository → Settings → Collaborators → Add people
```

### Pull Request Workflow

```bash
# Team member creates branch
git checkout -b feature/new-feature

# Makes changes and pushes
git push -u origin feature/new-feature

# Creates Pull Request on GitHub
# You review and approve
# Merge to main
```

### Code Review Checklist

- [ ] No secrets committed
- [ ] Tests pass
- [ ] Documentation updated
- [ ] Terraform validates
- [ ] Changes reviewed

---

## Syncing Multiple Environments

### Scenario: You have changes on your local machine and deployment server

```bash
# On local machine
git add .
git commit -m "Update FSx configuration"
git push origin main

# On deployment server
git pull origin main
cd terraform/environments/staging
terraform plan
terraform apply
```

### Scenario: You made changes directly on deployment server

```bash
# On deployment server
git add .
git commit -m "Emergency fix: Update security group"
git push origin main

# On local machine
git pull origin main
```

---

## Useful Git Aliases

Add to `~/.gitconfig`:

```ini
[alias]
    st = status
    co = checkout
    br = branch
    ci = commit
    unstage = reset HEAD --
    last = log -1 HEAD
    visual = log --oneline --graph --decorate --all
    amend = commit --amend --no-edit
```

Usage:
```bash
git st          # Instead of git status
git co main     # Instead of git checkout main
git visual      # Pretty commit history
```

---

## Troubleshooting

### Problem: Accidentally committed secrets

```bash
# Remove file from git history
git filter-branch --force --index-filter \
  "git rm --cached --ignore-unmatch terraform/environments/staging/terraform.tfvars" \
  --prune-empty --tag-name-filter cat -- --all

# Force push (⚠️ dangerous)
git push origin --force --all

# Rotate the exposed secrets immediately!
```

### Problem: Merge conflicts

```bash
# Pull latest
git pull origin main

# If conflicts occur
# Edit conflicted files
# Look for <<<<<<< HEAD markers

# After resolving
git add .
git commit -m "Resolve merge conflicts"
git push origin main
```

### Problem: Need to undo last commit

```bash
# Undo commit, keep changes
git reset --soft HEAD~1

# Undo commit, discard changes
git reset --hard HEAD~1
```

---

## Best Practices

### ✅ DO:
- Commit often with clear messages
- Use branches for features
- Review changes before committing (`git diff`)
- Pull before pushing
- Use `.gitignore` properly
- Tag releases (`git tag v1.0.0`)

### ❌ DON'T:
- Commit secrets or credentials
- Commit directly to main (use branches)
- Force push to main
- Commit large binary files
- Commit generated files (node_modules, .terraform)

---

## Quick Reference

```bash
# Setup
git init
git remote add origin <url>
git push -u origin main

# Daily workflow
git pull
git add .
git commit -m "message"
git push

# Branching
git checkout -b feature-name
git push -u origin feature-name

# Syncing
git pull origin main
git push origin main

# Viewing
git status
git log
git diff
```

---

## Next Steps

1. ✅ Initialize git repository
2. ✅ Create GitHub repository
3. ✅ Push code to GitHub
4. ✅ Clone on deployment server
5. ✅ Set up secrets securely
6. ✅ Deploy from GitHub

Your code is now version controlled and easily deployable! 🎉
