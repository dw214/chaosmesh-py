#!/bin/bash
# Update version script
# Usage: ./scripts/update-version.sh <new_version>
# Example: ./scripts/update-version.sh 0.1.1

set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

if [ -z "$1" ]; then
    echo -e "${RED}Error: Version number required${NC}"
    echo "Usage: $0 <version>"
    echo "Examples:"
    echo "  $0 0.1.1        # Patch release"
    echo "  $0 0.2.0        # Minor release"
    echo "  $0 1.0.0        # Major release"
    echo "  $0 0.1.0a1      # Alpha release"
    echo "  $0 0.1.0b1      # Beta release"
    echo "  $0 0.1.0rc1     # Release candidate"
    exit 1
fi

NEW_VERSION="$1"

# Validate version format
if ! echo "$NEW_VERSION" | grep -qE '^[0-9]+\.[0-9]+\.[0-9]+(a|b|rc)?[0-9]*$'; then
    echo -e "${RED}Error: Invalid version format${NC}"
    echo "Version should be in format: MAJOR.MINOR.PATCH[a|b|rc]N"
    echo "Examples: 0.1.0, 0.1.1, 1.0.0, 0.1.0a1, 0.1.0b1, 0.1.0rc1"
    exit 1
fi

CURRENT_VERSION=$(grep '^version' pyproject.toml | cut -d'"' -f2)

echo -e "${YELLOW}====================================${NC}"
echo -e "${YELLOW}   Version Update${NC}"
echo -e "${YELLOW}====================================${NC}"
echo ""
echo "Current version: $CURRENT_VERSION"
echo "New version:     $NEW_VERSION"
echo ""

# Update pyproject.toml
echo -e "${GREEN}[1/3] Updating pyproject.toml...${NC}"
if [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS
    sed -i '' "s/^version = \"$CURRENT_VERSION\"/version = \"$NEW_VERSION\"/" pyproject.toml
else
    # Linux
    sed -i "s/^version = \"$CURRENT_VERSION\"/version = \"$NEW_VERSION\"/" pyproject.toml
fi
echo "  ✓ Updated pyproject.toml"

# Update __init__.py
echo -e "${GREEN}[2/3] Updating chaos_sdk/__init__.py...${NC}"
if [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS
    sed -i '' "s/__version__ = \"$CURRENT_VERSION\"/__version__ = \"$NEW_VERSION\"/" chaos_sdk/__init__.py
else
    # Linux
    sed -i "s/__version__ = \"$CURRENT_VERSION\"/__version__ = \"$NEW_VERSION\"/" chaos_sdk/__init__.py
fi
echo "  ✓ Updated __init__.py"

# Verify
echo -e "${GREEN}[3/3] Verifying changes...${NC}"
TOML_VERSION=$(grep '^version' pyproject.toml | cut -d'"' -f2)
INIT_VERSION=$(grep '^__version__' chaos_sdk/__init__.py | cut -d'"' -f2)

if [ "$TOML_VERSION" = "$NEW_VERSION" ] && [ "$INIT_VERSION" = "$NEW_VERSION" ]; then
    echo -e "  ${GREEN}✓ Version updated successfully${NC}"
else
    echo -e "  ${RED}✗ Version mismatch detected${NC}"
    echo "    pyproject.toml: $TOML_VERSION"
    echo "    __init__.py: $INIT_VERSION"
    exit 1
fi

echo ""
echo -e "${GREEN}✓ Version updated to $NEW_VERSION${NC}"
echo ""
echo "Next steps:"
echo "1. Update CHANGELOG.md with changes"
echo "2. Review and commit:"
echo "   git add pyproject.toml chaos_sdk/__init__.py CHANGELOG.md"
echo "   git commit -m \"Bump version to $NEW_VERSION\""
echo "3. Test publish:"
echo "   ./scripts/publish.sh test"
echo "4. Publish to PyPI:"
echo "   ./scripts/publish.sh prod"
echo "5. Create and push tag:"
echo "   git tag v$NEW_VERSION"
echo "   git push origin v$NEW_VERSION"
