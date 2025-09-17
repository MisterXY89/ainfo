# Release Script Usage

The `release.sh` script automates the version bumping, committing, pushing, and tagging process for PyPI releases.

## Usage

```bash
./release.sh [BUMP_LEVEL]
```

## Bump Levels

- `0` = **patch** (x.x.X) - Bug fixes, small changes
- `1` = **minor** (x.X.0) - New features, backward compatible
- `2` = **major** (X.0.0) - Breaking changes

## Examples

```bash
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
7. 🤖 **Triggers** GitHub Actions to publish to PyPI

## Safety Features

- Checks for uncommitted changes (excludes `main.py` and `fetched_page.html`)
- Runs full test suite before proceeding (fails if tests don't pass)
- Confirms version bump with user before proceeding
- Validates version updates were successful
- Uses atomic operations (fails fast on any error)
- Shows colored output for better visibility

## Notes

- The script automatically excludes `main.py` and `fetched_page.html` from git operations
- GitHub Actions workflow should be configured to publish to PyPI on tag push
- Version format follows semantic versioning (MAJOR.MINOR.PATCH)