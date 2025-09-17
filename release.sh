#!/bin/bash

# Script to bump version, commit, push, and tag for PyPI release
# Usage: ./release.sh [BUMP_LEVEL]
# BUMP_LEVEL: 0 = patch (x.x.X), 1 = minor (x.X.0), 2 = major (X.0.0)

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if we're in a git repository
if ! git rev-parse --git-dir > /dev/null 2>&1; then
    print_error "Not in a git repository!"
    exit 1
fi

# Check for uncommitted changes (excluding main.py and fetched_page.html)
if ! git diff --quiet HEAD -- ':!main.py' ':!fetched_page.html'; then
    print_error "You have uncommitted changes! Please commit or stash them first."
    git status --porcelain | grep -v -E "(main\.py|fetched_page\.html)"
    exit 1
fi

# Run tests before proceeding
print_info "Running tests..."
if command -v pytest > /dev/null 2>&1; then
    if ! pytest -v; then
        print_error "Tests failed! Please fix them before releasing."
        exit 1
    fi
    print_info "✅ All tests passed!"
else
    print_warning "pytest not found, skipping tests"
fi

# Get bump level from argument or default to patch (0)
BUMP_LEVEL=${1:-0}

# Validate bump level
if ! [[ "$BUMP_LEVEL" =~ ^[0-2]$ ]]; then
    print_error "Invalid bump level: $BUMP_LEVEL"
    echo "Usage: $0 [BUMP_LEVEL]"
    echo "  0 = patch (x.x.X)"
    echo "  1 = minor (x.X.0)" 
    echo "  2 = major (X.0.0)"
    exit 1
fi

# Get current version from pyproject.toml
CURRENT_VERSION=$(grep '^version = ' pyproject.toml | sed 's/version = "\(.*\)"/\1/')

if [ -z "$CURRENT_VERSION" ]; then
    print_error "Could not find current version in pyproject.toml"
    exit 1
fi

print_info "Current version: $CURRENT_VERSION"

# Parse version components
IFS='.' read -r MAJOR MINOR PATCH <<< "$CURRENT_VERSION"

# Bump version based on level
case $BUMP_LEVEL in
    0) # Patch
        PATCH=$((PATCH + 1))
        BUMP_TYPE="patch"
        ;;
    1) # Minor
        MINOR=$((MINOR + 1))
        PATCH=0
        BUMP_TYPE="minor"
        ;;
    2) # Major
        MAJOR=$((MAJOR + 1))
        MINOR=0
        PATCH=0
        BUMP_TYPE="major"
        ;;
esac

NEW_VERSION="$MAJOR.$MINOR.$PATCH"
print_info "New version: $NEW_VERSION (${BUMP_TYPE} bump)"

# Confirm with user
read -p "Continue with version $NEW_VERSION? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    print_warning "Aborted by user"
    exit 1
fi

# Update pyproject.toml
print_info "Updating pyproject.toml..."
sed -i.bak "s/version = \"$CURRENT_VERSION\"/version = \"$NEW_VERSION\"/" pyproject.toml
rm pyproject.toml.bak

# Update src/ainfo/__init__.py
print_info "Updating src/ainfo/__init__.py..."
sed -i.bak "s/__version__ = \"$CURRENT_VERSION\"/__version__ = \"$NEW_VERSION\"/" src/ainfo/__init__.py
rm src/ainfo/__init__.py.bak

# Verify changes
print_info "Verifying version updates..."
PYPROJECT_VERSION=$(grep '^version = ' pyproject.toml | sed 's/version = "\(.*\)"/\1/')
INIT_VERSION=$(grep '^__version__ = ' src/ainfo/__init__.py | sed 's/__version__ = "\(.*\)"/\1/')

if [ "$PYPROJECT_VERSION" != "$NEW_VERSION" ] || [ "$INIT_VERSION" != "$NEW_VERSION" ]; then
    print_error "Version update failed!"
    print_error "pyproject.toml: $PYPROJECT_VERSION"
    print_error "__init__.py: $INIT_VERSION"
    print_error "Expected: $NEW_VERSION"
    exit 1
fi

print_info "Version updated successfully in both files"

# Stage the version files
print_info "Staging version files..."
git add pyproject.toml src/ainfo/__init__.py

# Create commit message based on bump type
case $BUMP_TYPE in
    "patch")
        COMMIT_MSG="chore: bump version to $NEW_VERSION (patch)"
        ;;
    "minor")
        COMMIT_MSG="feat: bump version to $NEW_VERSION (minor)"
        ;;
    "major")
        COMMIT_MSG="feat!: bump version to $NEW_VERSION (major)"
        ;;
esac

# Commit changes
print_info "Committing version bump..."
git commit -m "$COMMIT_MSG"

# Push to main
print_info "Pushing to main branch..."
git push origin main

# Create and push tag
TAG_NAME="v$NEW_VERSION"
print_info "Creating tag $TAG_NAME..."
git tag -a "$TAG_NAME" -m "Release $TAG_NAME"

print_info "Pushing tag to GitHub..."
git push origin "$TAG_NAME"

print_info "✅ Release process completed successfully!"
print_info "📦 Version $NEW_VERSION has been tagged and pushed"
print_info "🚀 GitHub Actions should now automatically publish to PyPI"

# Show final git status
print_info "Final git status:"
git status --porcelain | grep -v -E "(main\.py|fetched_page\.html)" || echo "Working directory clean (excluding main.py and fetched_page.html)"