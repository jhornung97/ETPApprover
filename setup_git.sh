#!/bin/bash
# Git Repository Setup Script for ETaPprover

set -e  # Exit on error

echo "========================================"
echo "ETaPprover - Git Repository Setup"
echo "========================================"
echo ""

# Check if git is installed
if ! command -v git &> /dev/null; then
    echo "❌ Error: git is not installed"
    echo "Please install git first: sudo apt-get install git"
    exit 1
fi

# Check if already a git repository
if [ -d ".git" ]; then
    echo "⚠️  Warning: This is already a git repository"
    read -p "Reinitialize? This will keep history. (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Aborted."
        exit 0
    fi
fi

echo "Step 1: Checking credentials.json..."
if [ -f "credentials.json" ]; then
    echo "✓ credentials.json found"
    
    # Check if credentials.json.example exists
    if [ ! -f "credentials.json.example" ]; then
        echo "⚠️  Creating credentials.json.example from template..."
        echo "⚠️  WARNING: Make sure credentials.json.example doesn't contain real credentials!"
        read -p "Press Enter to continue..."
    fi
    
    # Secure credentials.json
    chmod 600 credentials.json
    echo "✓ Set permissions: 600 (owner read/write only)"
else
    echo "❌ credentials.json not found"
    if [ -f "credentials.json.example" ]; then
        echo "   Please copy credentials.json.example to credentials.json and fill in your credentials"
        echo "   cp credentials.json.example credentials.json"
    fi
    exit 1
fi

echo ""
echo "Step 2: Initializing git repository..."
if [ ! -d ".git" ]; then
    git init
    echo "✓ Git repository initialized"
else
    echo "✓ Git repository already exists"
fi

echo ""
echo "Step 3: Setting up .gitignore..."
if [ -f ".gitignore" ]; then
    # Check if credentials.json is in .gitignore
    if grep -q "credentials.json" .gitignore; then
        echo "✓ credentials.json already in .gitignore"
    else
        echo "credentials.json" >> .gitignore
        echo "✓ Added credentials.json to .gitignore"
    fi
else
    echo "❌ .gitignore not found (this shouldn't happen)"
    exit 1
fi

echo ""
echo "Step 4: Verifying file structure..."
required_files=(
    "README.md"
    "requirements.txt"
    "credentials.json.example"
    ".gitignore"
    "CHANGELOG.md"
    "scrape.py"
    "test.py"
)

for file in "${required_files[@]}"; do
    if [ -f "$file" ]; then
        echo "  ✓ $file"
    else
        echo "  ❌ $file missing"
    fi
done

# Check directories
required_dirs=("docs" "tests")
for dir in "${required_dirs[@]}"; do
    if [ -d "$dir" ]; then
        echo "  ✓ $dir/"
    else
        echo "  ❌ $dir/ missing"
    fi
done

echo ""
echo "Step 5: Adding files to git..."
git add README.md
git add requirements.txt
git add credentials.json.example
git add .gitignore
git add CHANGELOG.md
git add scrape.py
git add test.py
git add docs/
git add tests/

echo "✓ Files staged for commit"

echo ""
echo "Step 6: Checking if credentials.json would be committed..."
if git ls-files --error-unmatch credentials.json 2>/dev/null; then
    echo "❌ WARNING: credentials.json is tracked by git!"
    echo "   Removing from git index..."
    git rm --cached credentials.json
    echo "✓ credentials.json removed from git tracking"
else
    echo "✓ credentials.json is not tracked (good!)"
fi

echo ""
echo "Step 7: Creating initial commit..."
read -p "Create initial commit? (Y/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Nn]$ ]]; then
    echo "Skipping commit. You can commit manually with:"
    echo "  git commit -m 'Initial commit: ETaPprover v2.0'"
else
    git commit -m "Initial commit: ETaPprover v2.0

- Smart username lookup system
- Cronjob support with log capture
- Email and Mattermost notifications
- Bachelor thesis filtering
- Comprehensive documentation
"
    echo "✓ Initial commit created"
fi

echo ""
echo "========================================"
echo "✅ Git setup complete!"
echo "========================================"
echo ""
echo "Next steps:"
echo ""
echo "1. Configure remote repository (if using GitHub/GitLab):"
echo "   git remote add origin <repository-url>"
echo "   git branch -M main"
echo "   git push -u origin main"
echo ""
echo "2. Verify credentials.json is NOT in git:"
echo "   git ls-files | grep credentials.json"
echo "   (should return nothing)"
echo ""
echo "3. Create a .git/info/exclude file for local ignores:"
echo "   echo '*.local' >> .git/info/exclude"
echo ""
echo "4. Set up git config (if not already done):"
echo "   git config user.name 'Your Name'"
echo "   git config user.email 'your.email@kit.edu'"
echo ""
echo "Happy coding! 🚀"
