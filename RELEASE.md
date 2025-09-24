# Release Script Usage

The `release.sh` script automates the version bumping, committing, pushing, tagging, and GitHub Release creation process for PyPI publishing.

## Usage

```bash
./release.sh [--dry-run] [BUMP_LEVEL]
```

## Requirements

The script needs to create GitHub Releases to trigger PyPI publishing. Choose one option:

### Option 1: GitHub CLI (Recommended)
```bash
# Install GitHub CLI
brew install gh  # macOS
# or download from https://cli.github.com/

# Authenticate
gh auth login
```

### Option 2: Personal Access Token
```bash
# Create token at https://github.com/settings/tokens
# Needs "repo" permissions for releases
export GITHUB_TOKEN="your_token_here"
```

## Bump Levels

- `0` = **patch** (x.x.X) - Bug fixes, small changes
- `1` = **minor** (x.X.0) - New features, backward compatible
- `2` = **major** (X.0.0) - Breaking changes

## Examples

```bash
# Test what would happen (dry-run mode)
./release.sh --dry-run 1

# Patch release (1.1.0 → 1.1.1)
./release.sh 0

# Minor release (1.1.0 → 1.2.0) 
./release.sh 1

# Major release (1.1.0 → 2.0.0)
./release.sh 2

# Default is patch if no argument provided
./release.sh
```

## What the script does

1. ✅ **Validates** environment (git repo, no uncommitted changes)
2. 🧪 **Runs tests** with pytest (fails if tests don't pass)
3. 🔢 **Bumps version** in `pyproject.toml` and `src/ainfo/__init__.py`
4. 📝 **Commits** the version bump with appropriate message
5. 🚀 **Pushes** to main branch
6. 🏷️ **Creates and pushes** git tag (e.g., `v1.1.1`)
7. 📦 **Creates GitHub Release** (required to trigger PyPI publishing)
8. 🤖 **Triggers** GitHub Actions to publish to PyPI automatically

## Safety Features

- Checks for uncommitted changes (excludes `main.py` and `fetched_page.html`)
- Runs full test suite before proceeding (fails if tests don't pass)
- Confirms version bump with user before proceeding
- Validates version updates were successful
- Uses atomic operations (fails fast on any error)
- Shows colored output for better visibility

## Important Notes

- **GitHub Release is required**: The PyPI publishing workflow triggers on `release: types: [published]`, not git tags
- Git tags alone will NOT trigger PyPI publishing
- The script automatically excludes `main.py` and `fetched_page.html` from git operations
- Version format follows semantic versioning (MAJOR.MINOR.PATCH)
- Use `--dry-run` to test changes before executing

## Troubleshooting

### PyPI not publishing after release
- Verify the GitHub Release was created (not just the git tag)
- Check GitHub Actions workflow status
- Ensure PyPI trusted publishing is configured

### "GITHUB_TOKEN not set" error
```bash
# Option 1: Install GitHub CLI
brew install gh && gh auth login

# Option 2: Set environment variable
export GITHUB_TOKEN="ghp_your_token_here"
```

### Manual release creation
If the script fails to create a GitHub Release, create one manually:
1. Go to https://github.com/MisterXY89/ainfo/releases
2. Click "Create a new release"
3. Select the existing tag (e.g., `v1.2.1`)
4. Publish the release to trigger PyPI publishing