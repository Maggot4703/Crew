#!/bin/bash

set -e
echo "Disk Space Cleanup Utility"
echo "=========================="

# Show current disk usage
echo "Current disk usage:"
df -h /

# Function to ask for confirmation
confirm() {
    read -p "$1 (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        return 0
    fi
    return 1
}

# Clean package caches
clean_package_cache() {
    if command -v apt-get &> /dev/null; then
        echo "Cleaning APT cache..."
        sudo apt-get clean
        sudo apt-get autoremove --yes
    elif command -v dnf &> /dev/null; then
        echo "Cleaning DNF cache..."
        sudo dnf clean all
    elif command -v yum &> /dev/null; then
        echo "Cleaning YUM cache..."
        sudo yum clean all
    elif command -v pacman &> /dev/null; then
        echo "Cleaning Pacman cache..."
        sudo pacman -Sc --noconfirm
    fi
}

# Clean npm cache
clean_npm_cache() {
    if command -v npm &> /dev/null; then
        echo "Cleaning npm cache..."
        npm cache clean --force
    fi
}

# Clean pip cache
clean_pip_cache() {
    if command -v pip &> /dev/null; then
        echo "Cleaning pip cache..."
        pip cache purge
    fi
}

# Clean Docker
clean_docker() {
    if command -v docker &> /dev/null; then
        echo "Cleaning Docker..."
        docker system prune -f
    fi
}

# Clean temporary files
clean_temp() {
    echo "Cleaning temporary files..."
    sudo rm -rf /tmp/*
    sudo rm -rf /var/tmp/*
}

# Clean VSCode related caches
clean_vscode_cache() {
    echo "Cleaning VSCode caches..."
    rm -rf ~/.vscode/extensions/**/node_modules/.cache
    rm -rf ~/.vscode-server/extensions/**/node_modules/.cache
    rm -rf ~/.config/Code/User/workspaceStorage/**/node_modules/.cache
}

# Find large files
find_large_files() {
    echo "Finding files larger than 500MB..."
    sudo find / -type f -size +500M -exec ls -lh {} \; 2>/dev/null | sort -k5 -hr
}

# Find large directories
find_large_directories() {
    echo "Finding largest directories in home..."
    du -h --max-depth=2 ~ | sort -hr | head -20
}

# Main menu
echo
echo "Select an option:"
echo "1) Clean package caches (apt, dnf, etc.)"
echo "2) Clean npm cache"
echo "3) Clean pip cache"
echo "4) Clean Docker unused images and containers"
echo "5) Clean temporary files"
echo "6) Clean VSCode caches"
echo "7) Find large files (>500MB)"
echo "8) Find large directories"
echo "9) Run all cleaning options"
echo "0) Exit"

read -p "Choose an option (0-9): " choice

case $choice in
    1) clean_package_cache ;;
    2) clean_npm_cache ;;
    3) clean_pip_cache ;;
    4) clean_docker ;;
    5) clean_temp ;;
    6) clean_vscode_cache ;;
    7) find_large_files ;;
    8) find_large_directories ;;
    9)
        if confirm "This will run all cleaning operations. Continue?"; then
            clean_package_cache
            clean_npm_cache
            clean_pip_cache
            clean_docker
            clean_temp
            clean_vscode_cache
        fi
        ;;
    0) echo "Exiting." ;;
    *) echo "Invalid option." ;;
esac

# Show new disk usage
echo
echo "New disk usage:"
df -h /
