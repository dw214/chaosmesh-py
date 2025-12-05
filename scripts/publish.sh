#!/bin/bash
# Quick publish script for PyPI release
# Usage: ./scripts/publish.sh [test|prod]

set -e

# Color output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

MODE=${1:-test}

echo -e "${YELLOW}====================================${NC}"
echo -e "${YELLOW}   Chaos SDK Publishing Script${NC}"
echo -e "${YELLOW}====================================${NC}"
echo ""

# Check if build tools are installed
echo -e "${GREEN}[1/7] Checking dependencies...${NC}"
if ! command -v python &> /dev/null; then
    echo -e "${RED}Error: python not found${NC}"
    exit 1
fi

pip show build > /dev/null 2>&1 || pip install --upgrade build
pip show twine > /dev/null 2>&1 || pip install --upgrade twine

# Clean old builds
echo -e "${GREEN}[2/7] Cleaning old builds...${NC}"
rm -rf dist/ build/ *.egg-info chaos_sdk.egg-info

# Build package
echo -e "${GREEN}[3/7] Building package...${NC}"
python -m build

# Check package
echo -e "${GREEN}[4/7] Checking package...${NC}"
twine check dist/*

# Show package info
echo ""
echo -e "${YELLOW}Package contents:${NC}"
ls -lh dist/

# Upload
if [ "$MODE" = "test" ]; then
    echo ""
    echo -e "${YELLOW}[5/7] Uploading to TestPyPI...${NC}"
    echo -e "${YELLOW}Repository: https://test.pypi.org${NC}"
    python -m twine upload --repository testpypi dist/*
    
    echo ""
    echo -e "${GREEN}✓ Successfully uploaded to TestPyPI!${NC}"
    echo ""
    echo -e "${YELLOW}To install from TestPyPI:${NC}"
    echo "  pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ chaos-sdk"
    echo ""
    echo -e "${YELLOW}View on TestPyPI:${NC}"
    echo "  https://test.pypi.org/project/chaos-sdk/"
    
elif [ "$MODE" = "prod" ]; then
    echo ""
    echo -e "${RED}[5/7] WARNING: Uploading to PRODUCTION PyPI!${NC}"
    echo -e "${RED}This action cannot be undone. Version numbers cannot be reused.${NC}"
    read -p "Are you sure you want to continue? (yes/no): " confirm
    
    if [ "$confirm" != "yes" ]; then
        echo -e "${YELLOW}Upload cancelled.${NC}"
        exit 0
    fi
    
    python -m twine upload dist/*
    
    echo ""
    echo -e "${GREEN}✓ Successfully uploaded to PyPI!${NC}"
    echo ""
    echo -e "${YELLOW}To install:${NC}"
    echo "  pip install chaos-sdk"
    echo ""
    echo -e "${YELLOW}View on PyPI:${NC}"
    echo "  https://pypi.org/project/chaos-sdk/"
else
    echo -e "${RED}Error: Invalid mode. Use 'test' or 'prod'${NC}"
    exit 1
fi

echo ""
echo -e "${GREEN}[6/7] Verification${NC}"
echo "Package name: chaos-sdk"
echo "Version: $(grep '^version' pyproject.toml | cut -d'"' -f2)"
echo ""

echo -e "${GREEN}[7/7] Next steps:${NC}"
echo "1. Test installation in a clean environment"
echo "2. Verify imports work correctly"
echo "3. Update CHANGELOG.md"
echo "4. Create git tag: git tag v$(grep '^version' pyproject.toml | cut -d'\"' -f2)"
echo "5. Push tags: git push origin --tags"
echo ""
echo -e "${GREEN}✓ Done!${NC}"
