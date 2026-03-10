#!/bin/bash
set -euo pipefail

echo "=== StoryWeave VM Setup ==="
echo ""

# 1. Update system
echo "[1/5] Updating system packages..."
sudo apt-get update -y && sudo apt-get upgrade -y

# 2. Install Docker
echo "[2/5] Installing Docker..."
sudo apt-get install -y ca-certificates curl gnupg
sudo install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
sudo chmod a+r /etc/apt/keyrings/docker.gpg
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
  $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
sudo apt-get update -y
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

# 3. Add current user to docker group (no sudo needed for docker commands)
echo "[3/5] Configuring Docker permissions..."
sudo usermod -aG docker $USER

# 4. Create app directory
echo "[4/5] Creating application directory..."
sudo mkdir -p /opt/storyweave
sudo chown $USER:$USER /opt/storyweave

# 5. Enable Docker on boot
echo "[5/5] Enabling Docker service..."
sudo systemctl enable docker
sudo systemctl start docker

echo ""
echo "=== Setup complete! ==="
echo ""
echo "IMPORTANT: Log out and log back in for Docker group permissions to take effect."
echo "Then run: cd /opt/storyweave && bash deploy.sh"
