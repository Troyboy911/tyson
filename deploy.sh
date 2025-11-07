#!/bin/bash
# Tyson Agent VPS Deployment Script
# Run this on your Ubuntu VPS

set -e  # Exit on error

echo "===================================="
echo "Tyson Agent Deployment Script"
echo "===================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo -e "${RED}Please run as root (use: sudo bash deploy.sh)${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Running as root${NC}"

# Update system
echo ""
echo "Updating system packages..."
apt-get update -qq

# Install Python if not present
if ! command -v python3 &> /dev/null; then
    echo "${YELLOW}Python3 not found. Installing...${NC}"
    apt-get install -y python3 python3-pip python3-venv
    echo -e "${GREEN}✓ Python3 installed${NC}"
else
    PYTHON_VERSION=$(python3 --version)
    echo -e "${GREEN}✓ Python3 already installed: $PYTHON_VERSION${NC}"
fi

# Install git if not present
if ! command -v git &> /dev/null; then
    echo "${YELLOW}Git not found. Installing...${NC}"
    apt-get install -y git
    echo -e "${GREEN}✓ Git installed${NC}"
else
    echo -e "${GREEN}✓ Git already installed${NC}"
fi

# Create app directory
APP_DIR="/opt/tyson"
echo ""
echo "Setting up application directory: $APP_DIR"

if [ -d "$APP_DIR" ]; then
    echo "${YELLOW}Directory exists. Backing up...${NC}"
    mv $APP_DIR ${APP_DIR}_backup_$(date +%Y%m%d_%H%M%S)
fi

mkdir -p $APP_DIR
cd $APP_DIR

# Clone repository
echo ""
echo "Cloning Tyson repository..."
git clone https://github.com/Troyboy911/tyson.git .
echo -e "${GREEN}✓ Repository cloned${NC}"

# Create virtual environment
echo ""
echo "Creating Python virtual environment..."
python3 -m venv venv
source venv/bin/activate
echo -e "${GREEN}✓ Virtual environment created${NC}"

# Install dependencies
echo ""
echo "Installing Python dependencies..."
pip install --upgrade pip -q
pip install -r requirements.txt -q
echo -e "${GREEN}✓ Dependencies installed${NC}"

# Set up environment file
echo ""
echo "Setting up environment variables..."
if [ ! -f ".env" ]; then
    cat > .env << 'EOF'
# Perplexity API Configuration
PERPLEXITY_API_KEY=your_perplexity_api_key_here
EOF
    echo -e "${YELLOW}⚠ Please edit /opt/tyson/.env and add your Perplexity API key${NC}"
    echo -e "${YELLOW}  Run: nano /opt/tyson/.env${NC}"
else
    echo -e "${GREEN}✓ .env file already exists${NC}"
fi

# Create systemd service
echo ""
echo "Creating systemd service..."
cat > /etc/systemd/system/tyson.service << EOF
[Unit]
Description=Tyson Perplexity AI Agent
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/tyson
Environment="PATH=/opt/tyson/venv/bin"
EnvironmentFile=/opt/tyson/.env
ExecStart=/opt/tyson/venv/bin/python3 /opt/tyson/agent.py
Restart=always
RestartSec=10
StandardOutput=append:/var/log/tyson.log
StandardError=append:/var/log/tyson-error.log

[Install]
WantedBy=multi-user.target
EOF

echo -e "${GREEN}✓ Systemd service created${NC}"

# Create log files
touch /var/log/tyson.log
touch /var/log/tyson-error.log
chmod 644 /var/log/tyson*.log

# Reload systemd
systemctl daemon-reload

echo ""
echo -e "${GREEN}====================================="
echo "✓ Deployment Complete!${NC}"
echo "====================================="
echo ""
echo "Next steps:"
echo "1. Edit your API key:"
echo "   nano /opt/tyson/.env"
echo ""
echo "2. Start the service:"
echo "   systemctl start tyson"
echo ""
echo "3. Enable auto-start on boot:"
echo "   systemctl enable tyson"
echo ""
echo "4. Check status:"
echo "   systemctl status tyson"
echo ""
echo "5. View logs:"
echo "   tail -f /var/log/tyson.log"
echo ""
echo "Useful commands:"
echo "  systemctl restart tyson  # Restart service"
echo "  systemctl stop tyson     # Stop service"
echo "  journalctl -u tyson -f   # View live logs"
echo ""

# Check Easypanel and Traefik
echo -e "${YELLOW}Checking Easypanel and Traefik configuration...${NC}"
echo ""

if command -v docker &> /dev/null; then
    echo -e "${GREEN}✓ Docker installed${NC}"
    
    # Check running containers
    echo ""
    echo "Running Docker containers:"
    docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
    
    # Check for Traefik
    if docker ps | grep -q traefik; then
        echo -e "\n${GREEN}✓ Traefik is running${NC}"
        echo ""
        echo "Traefik container details:"
        docker ps --filter "name=traefik" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
    else
        echo -e "\n${RED}✗ Traefik not found in running containers${NC}"
    fi
    
    # Check Easypanel
    if docker ps | grep -q easypanel; then
        echo -e "\n${GREEN}✓ Easypanel is running${NC}"
    else
        echo -e "\n${YELLOW}⚠ Easypanel not found in running containers${NC}"
    fi
else
    echo -e "${RED}✗ Docker not installed${NC}"
fi

echo ""
echo -e "${YELLOW}For Traefik/Easypanel troubleshooting, run:${NC}"
echo "  bash /opt/tyson/troubleshoot_traefik.sh"
echo ""
