#!/bin/bash
# VPS Auto-Fix Script for Easypanel/Traefik/Docker
# This script diagnoses and fixes common issues

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}"
echo "=========================================="
echo "  VPS Auto-Fix & Diagnostic Tool"
echo "=========================================="
echo -e "${NC}"

# Check root
if [ "$EUID" -ne 0 ]; then 
    echo -e "${RED}Please run as root: sudo bash fix_vps.sh${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Running as root${NC}\n"

# Function to check and fix
check_fix() {
    local service=$1
    local fix_cmd=$2
    echo -e "${YELLOW}Checking $service...${NC}"
    if eval "$fix_cmd"; then
        echo -e "${GREEN}✓ $service OK${NC}\n"
        return 0
    else
        echo -e "${RED}✗ $service has issues${NC}\n"
        return 1
    fi
}

# 1. Check Docker
echo -e "${BLUE}[1/10] Checking Docker${NC}"
if ! command -v docker &> /dev/null; then
    echo -e "${YELLOW}Docker not found. Installing...${NC}"
    curl -fsSL https://get.docker.com -o get-docker.sh
    sh get-docker.sh
    rm get-docker.sh
    systemctl start docker
    systemctl enable docker
    echo -e "${GREEN}✓ Docker installed${NC}\n"
else
    echo -e "${GREEN}✓ Docker installed${NC}"
    docker --version
    echo ""
fi

# 2. Check Docker service
echo -e "${BLUE}[2/10] Checking Docker service${NC}"
if ! systemctl is-active --quiet docker; then
    echo -e "${YELLOW}Docker service not running. Starting...${NC}"
    systemctl start docker
    echo -e "${GREEN}✓ Docker started${NC}\n"
else
    echo -e "${GREEN}✓ Docker service running${NC}\n"
fi

# 3. List all containers
echo -e "${BLUE}[3/10] Listing Docker containers${NC}"
echo "Running containers:"
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" || echo "None"
echo ""
echo "All containers (including stopped):"
docker ps -a --format "table {{.Names}}\t{{.Status}}" || echo "None"
echo ""

# 4. Check Traefik
echo -e "${BLUE}[4/10] Checking Traefik${NC}"
if docker ps | grep -q traefik; then
    echo -e "${GREEN}✓ Traefik is running${NC}"
    docker ps --filter "name=traefik" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
    echo ""
    echo "Traefik logs (last 20 lines):"
    docker logs traefik --tail 20 2>&1 | tail -20
    echo ""
else
    echo -e "${RED}✗ Traefik not running${NC}"
    echo "Checking if Traefik container exists..."
    if docker ps -a | grep -q traefik; then
        echo -e "${YELLOW}Traefik container exists but stopped. Starting...${NC}"
        docker start traefik
        sleep 2
        if docker ps | grep -q traefik; then
            echo -e "${GREEN}✓ Traefik started${NC}\n"
        else
            echo -e "${RED}✗ Failed to start Traefik. Check logs:${NC}"
            docker logs traefik --tail 50
            echo ""
        fi
    else
        echo -e "${YELLOW}Traefik container not found${NC}"
        echo "This might be managed by Easypanel"
        echo ""
    fi
fi

# 5. Check Easypanel
echo -e "${BLUE}[5/10] Checking Easypanel${NC}"
if docker ps | grep -q easypanel; then
    echo -e "${GREEN}✓ Easypanel is running${NC}"
    docker ps --filter "name=easypanel" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
    echo ""
else
    echo -e "${RED}✗ Easypanel not running${NC}"
    if docker ps -a | grep -q easypanel; then
        echo -e "${YELLOW}Easypanel container exists but stopped. Starting...${NC}"
        docker start easypanel
        sleep 2
        if docker ps | grep -q easypanel; then
            echo -e "${GREEN}✓ Easypanel started${NC}\n"
        else
            echo -e "${RED}✗ Failed to start Easypanel${NC}\n"
        fi
    else
        echo -e "${YELLOW}Easypanel not installed${NC}"
        echo "To install Easypanel, run:"
        echo "  curl -sSL https://get.easypanel.io | sh"
        echo ""
    fi
fi

# 6. Check ports
echo -e "${BLUE}[6/10] Checking open ports${NC}"
echo "Ports in use:"
netstat -tulpn | grep LISTEN | grep -E ':(80|443|3000|8080|9000)' || echo "Common ports not in use"
echo ""

# 7. Check firewall
echo -e "${BLUE}[7/10] Checking firewall (UFW)${NC}"
if command -v ufw &> /dev/null; then
    ufw_status=$(ufw status | head -1)
    echo "UFW Status: $ufw_status"
    if echo "$ufw_status" | grep -q "inactive"; then
        echo -e "${YELLOW}UFW is inactive. This is OK but not recommended${NC}"
    else
        echo "UFW rules:"
        ufw status numbered | grep -E '(80|443|22)' || echo "No rules for ports 80, 443, 22"
        echo ""
        echo -e "${YELLOW}Ensuring ports 80, 443, 22 are open...${NC}"
        ufw allow 80/tcp
        ufw allow 443/tcp
        ufw allow 22/tcp
        echo -e "${GREEN}✓ Firewall rules updated${NC}"
    fi
else
    echo -e "${YELLOW}UFW not installed${NC}"
    echo "To install: apt-get install ufw"
fi
echo ""

# 8. Check Docker networks
echo -e "${BLUE}[8/10] Checking Docker networks${NC}"
echo "Docker networks:"
docker network ls
echo ""

# 9. Restart problematic containers
echo -e "${BLUE}[9/10] Restarting containers if needed${NC}"
for container in $(docker ps -a --filter "status=exited" --format "{{.Names}}"); do
    echo -e "${YELLOW}Restarting stopped container: $container${NC}"
    docker restart $container
done
echo -e "${GREEN}✓ All stopped containers restarted${NC}\n"

# 10. System info
echo -e "${BLUE}[10/10] System Information${NC}"
echo "OS: $(lsb_release -d | cut -f2)"
echo "Kernel: $(uname -r)"
echo "Memory:"
free -h | grep Mem
echo ""
echo "Disk:"
df -h / | tail -1
echo ""

# Summary
echo -e "${GREEN}"
echo "=========================================="
echo "  Diagnostic Complete"
echo "=========================================="
echo -e "${NC}"

echo -e "${YELLOW}Quick Actions:${NC}"
echo ""
echo "View Traefik logs:"
echo "  docker logs traefik -f"
echo ""
echo "View Easypanel logs:"
echo "  docker logs easypanel -f"
echo ""
echo "Restart all containers:"
echo "  docker restart \$(docker ps -aq)"
echo ""
echo "Check if ports 80/443 are accessible from outside:"
echo "  curl -I http://89.116.159.31"
echo "  curl -I https://89.116.159.31"
echo ""

# Traefik specific checks
if docker ps | grep -q traefik; then
    echo -e "${BLUE}Traefik Configuration Check:${NC}"
    echo ""
    
    # Check Traefik config
    echo "Checking Traefik configuration files..."
    if [ -f "/etc/traefik/traefik.yml" ]; then
        echo "Found /etc/traefik/traefik.yml"
        echo "Content:"
        cat /etc/traefik/traefik.yml
    elif [ -f "/etc/traefik/traefik.yaml" ]; then
        echo "Found /etc/traefik/traefik.yaml"
        cat /etc/traefik/traefik.yaml
    else
        echo "No Traefik config found in /etc/traefik/"
        echo "Traefik might be configured via Docker labels or command line"
    fi
    echo ""
    
    # Check Traefik dashboard
    echo "Checking if Traefik dashboard is accessible..."
    traefik_ports=$(docker port traefik 2>/dev/null || echo "No ports exposed")
    echo "Traefik ports: $traefik_ports"
    echo ""
fi

echo -e "${GREEN}All checks complete!${NC}"
echo ""
echo -e "${YELLOW}If you're still having issues:${NC}"
echo "1. Check if your domain DNS points to 89.116.159.31"
echo "2. Verify SSL certificates are valid"
echo "3. Check Easypanel UI at http://89.116.159.31:3000"
echo "4. Review application logs in Easypanel dashboard"
echo ""
echo -e "${BLUE}Need more help? Run: docker ps -a && docker logs <container_name>${NC}"
echo ""
