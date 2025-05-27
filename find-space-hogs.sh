#!/bin/bash

set -e
echo "Disk Space Analysis Tool"
echo "======================="

# Function to check directory size
dir_size() {
    du -sh "$1" 2>/dev/null | cut -f1
}

# Check common space hogs
echo "Checking common space hogs..."

echo -n "VSCode extensions cache: "
dir_size ~/.vscode

echo -n "Node modules: "
find ~ -name "node_modules" -type d -prune -exec du -sh {} \; 2>/dev/null | sort -hr | head -10

echo -n "Docker: "
dir_size /var/lib/docker

echo -n "Package manager caches: "
dir_size /var/cache/apt
dir_size /var/cache/pacman

echo -n "Browser profiles/caches: "
dir_size ~/.config/google-chrome
dir_size ~/.mozilla
dir_size ~/.cache/google-chrome

echo -n "Downloads folder: "
dir_size ~/Downloads

echo -n "Virtual machines: "
dir_size ~/VirtualBox\ VMs
dir_size ~/.local/share/virtualbox

echo -n "Log files: "
dir_size /var/log

echo -n "Trash: "
dir_size ~/.local/share/Trash

# Check for large git repositories with large files
echo
echo "Checking for Git repositories with large pack files..."
find ~ -name "*.pack" -size +100M -exec ls -lh {} \; 2>/dev/null

# Find duplicate files
echo
echo "To find duplicate files, consider installing fdupes:"
echo "sudo apt install fdupes  # For Debian/Ubuntu"
echo "Then run: fdupes -r -S /path/to/check"

echo
echo "For more detailed analysis, consider installing ncdu:"
echo "sudo apt install ncdu  # For Debian/Ubuntu"
echo "Then run: ncdu /path/to/analyze"

echo
echo "You can run this script with sudo to check system directories"
