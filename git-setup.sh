#!/bin/bash

# RobCo Forge - Git Setup Script
# This script helps you set up Git and push to GitHub

set -e

# Colors
BLUE='\033[0;34m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}RobCo Forge - Git Setup${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Check if git is installed
if ! command -v git &> /dev/null; then
    echo -e "${YELLOW}⚠${NC} Git is not installed. Please install Git first."
    exit 1
fi

echo -e "${GREEN}✓${NC} Git is installed"
echo ""

# Check if already a git repository
if [ -d ".git" ]; then
    echo -e "${YELLOW}⚠${NC} This is already a Git repository"
    echo ""
    read -p "Do you want to continue? (yes/no): " CONTINUE
    if [ "$CONTINUE" != "yes" ]; then
        echo "Exiting..."
        exit 0
    fi
else
    # Initialize git repository
    echo -e "${BLUE}ℹ${NC} Initializing Git repository..."
    git init
    echo -e "${GREEN}✓${NC} Git repository initialized"
    echo ""
fi

# Create .gitignore if it doesn't exist
if [ ! -f ".gitignore" ]; then
    echo -e "${YELLOW}⚠${NC} .gitignore not found. Please create one first."
    exit 1
fi

echo -e "${GREEN}✓${NC} .gitignore found"
echo ""

# Check for sensitive files
echo -e "${BLUE}ℹ${NC} Checking for sensitive files..."
SENSITIVE_FILES=$(git status --porcelain | grep -E "\.tfvars$|\.env$|\.pem$|\.key$" || true)

if [ ! -z "$SENSITIVE_FILES" ]; then
    echo -e "${YELLOW}⚠${NC} WARNING: Found potentially sensitive files:"
    echo "$SENSITIVE_FILES"
    echo ""
    echo "These files should be in .gitignore!"
    read -p "Continue anyway? (yes/no): " CONTINUE
    if [ "$CONTINUE" != "yes" ]; then
        echo "Exiting..."
        exit 0
    fi
fi

# Add all files
echo -e "${BLUE}ℹ${NC} Adding files to Git..."
git add .
echo -e "${GREEN}✓${NC} Files added"
echo ""

# Show what will be committed
echo -e "${BLUE}ℹ${NC} Files to be committed:"
git status --short
echo ""

# Create initial commit
read -p "Create initial commit? (yes/no): " CREATE_COMMIT
if [ "$CREATE_COMMIT" = "yes" ]; then
    git commit -m "Initial commit: RobCo Forge platform v1.0.0

- Complete infrastructure (Terraform + CDK)
- API services (FastAPI)
- Lucy AI service
- Cost engine
- CLI tool
- Web portal (Next.js)
- Complete documentation
- Deployment scripts"
    
    echo -e "${GREEN}✓${NC} Initial commit created"
    echo ""
    
    # Create tag
    git tag -a v1.0.0 -m "Version 1.0.0 - Production ready"
    echo -e "${GREEN}✓${NC} Tag v1.0.0 created"
    echo ""
fi

# GitHub setup
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}GitHub Setup${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

echo "To push to GitHub, you need to:"
echo "1. Create a repository on GitHub: https://github.com/new"
echo "2. Name it: robco-forge"
echo "3. Make it Private (recommended)"
echo "4. DO NOT initialize with README, .gitignore, or license"
echo ""

read -p "Have you created the GitHub repository? (yes/no): " REPO_CREATED

if [ "$REPO_CREATED" = "yes" ]; then
    echo ""
    read -p "Enter your GitHub username: " GITHUB_USER
    read -p "Use SSH (recommended) or HTTPS? (ssh/https): " PROTOCOL
    
    if [ "$PROTOCOL" = "ssh" ]; then
        REMOTE_URL="git@github.com:${GITHUB_USER}/robco-forge.git"
    else
        REMOTE_URL="https://github.com/${GITHUB_USER}/robco-forge.git"
    fi
    
    echo ""
    echo -e "${BLUE}ℹ${NC} Adding remote: $REMOTE_URL"
    
    # Check if remote already exists
    if git remote | grep -q "origin"; then
        echo -e "${YELLOW}⚠${NC} Remote 'origin' already exists"
        read -p "Remove and re-add? (yes/no): " REMOVE_REMOTE
        if [ "$REMOVE_REMOTE" = "yes" ]; then
            git remote remove origin
            git remote add origin "$REMOTE_URL"
        fi
    else
        git remote add origin "$REMOTE_URL"
    fi
    
    echo -e "${GREEN}✓${NC} Remote added"
    echo ""
    
    # Push to GitHub
    read -p "Push to GitHub now? (yes/no): " PUSH_NOW
    if [ "$PUSH_NOW" = "yes" ]; then
        echo ""
        echo -e "${BLUE}ℹ${NC} Pushing to GitHub..."
        git branch -M main
        git push -u origin main
        git push --tags
        echo ""
        echo -e "${GREEN}✓${NC} Pushed to GitHub!"
        echo ""
        echo "View your repository at:"
        echo "https://github.com/${GITHUB_USER}/robco-forge"
    fi
fi

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Git Setup Complete!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo "Next steps:"
echo "1. Clone on deployment server:"
echo "   git clone https://github.com/${GITHUB_USER}/robco-forge.git"
echo ""
echo "2. Create terraform.tfvars with real secrets"
echo ""
echo "3. Deploy:"
echo "   cd terraform/environments/staging"
echo "   terraform init"
echo "   terraform apply"
echo ""
echo "See GIT_SETUP_GUIDE.md for more details"
echo ""
