#!/bin/bash

# ===============================
# Automated Deployment Script
# ===============================

set -e  # Exit on error

# === CONFIGURATION ===
GIT_REPO="https://github.com/AronTheAron/ACIT3855-Project.git"
REMOTE_USER="azureuser"
REMOTE_HOST="aw-project3855-w2025.eastus2.cloudapp.azure.com"
PROJECT_DIR="ACIT3855-Project"
SSH="$REMOTE_USER@$REMOTE_HOST"

echo "=== Connecting to VM and deploying project ==="

ssh $SSH << EOF

  set -e

  echo ">> Updating system..."
  sudo apt update && sudo apt install -y git docker.io docker-compose

  echo ">> Cleaning up old project (if any)..."
  rm -rf ~/$PROJECT_DIR

  echo ">> Cloning latest project from GitHub..."
  git clone $GIT_REPO

  cd $PROJECT_DIR

  echo ">> Making sure all folders exist..."
  mkdir -p logs data config/db

  echo ">> Rebuilding Docker containers..."
  docker compose down
  docker compose build
  docker compose up -d

  echo ">> Done! Services are up and running."
EOF

echo "✅ Deployment complete!"
