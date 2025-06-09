# GitHub Setup Troubleshooting

## Common Push Issues and Solutions

### 1. Repository doesn't exist
```bash
# Create repository on GitHub.com first, then:
git remote set-url origin https://github.com/YOUR_USERNAME/Crew.git
```

### 2. Authentication failed
```bash
# Use Personal Access Token instead of password
# Go to GitHub Settings > Developer settings > Personal access tokens
# Generate new token with 'repo' permissions
# Use token as password when prompted
```

### 3. Force push (use with caution)
```bash
git push -u origin main --force
```

### 4. Manual setup
```bash
# Initialize and set up manually
git init
git add .
git commit -m "Initial commit"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/Crew.git
git push -u origin main
```

### 5. Check current setup
```bash
git remote -v
git branch
git status
```
