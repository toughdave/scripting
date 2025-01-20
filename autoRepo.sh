#!/bin/bash

# GitHub username
GITHUB_USER="toughdave"

# Get repository name from argument or prompt
repoName=$1
while [ -z "$repoName" ]
do
    echo "Please provide a repository name"
    read -r -p "Repository Name: " repoName
done

# Create README file
echo "# $repoName" >> README.md

# Initialize git
git init
git add .
git commit -m "First commit"

# Create repository on GitHub using SSH key authentication
# Note: Make sure you have gh cli installed: sudo apt install gh
# And authenticated: gh auth login
gh repo create "$repoName" --public --confirm

# Configure remote with SSH URL
git branch -M main
git remote add origin "git@github.com:$GITHUB_USER/$repoName.git"
git push -u origin main