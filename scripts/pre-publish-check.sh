#!/bin/bash
# Pre-publish checklist script
# Run this before publishing to ensure everything is ready

set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${YELLOW}====================================${NC}"
echo -e "${YELLOW}   Pre-Publish Checklist${NC}"
echo -e "${YELLOW}====================================${NC}"
echo ""

ERRORS=0
WARNINGS=0

# Check 1: Version consistency
echo -e "${GREEN}[1/10] Checking version consistency...${NC}"
TOML_VERSION=$(grep '^version' pyproject.toml | cut -d'"' -f2)
INIT_VERSION=$(grep '^__version__' chaos_sdk/__init__.py | cut -d'"' -f2)

if [ "$TOML_VERSION" = "$INIT_VERSION" ]; then
    echo "  ✓ Version: $TOML_VERSION"
else
    echo -e "  ${RED}✗ Version mismatch!${NC}"
    echo "    pyproject.toml: $TOML_VERSION"
    echo "    __init__.py: $INIT_VERSION"
    ERRORS=$((ERRORS + 1))
fi

# Check 2: README exists
echo -e "${GREEN}[2/10] Checking README...${NC}"
if [ -f "README.md" ]; then
    echo "  ✓ README.md exists"
else
    echo -e "  ${RED}✗ README.md not found${NC}"
    ERRORS=$((ERRORS + 1))
fi

# Check 3: LICENSE exists
echo -e "${GREEN}[3/10] Checking LICENSE...${NC}"
if [ -f "LICENSE" ]; then
    echo "  ✓ LICENSE exists"
else
    echo -e "  ${YELLOW}⚠ LICENSE not found${NC}"
    WARNINGS=$((WARNINGS + 1))
fi

# Check 4: CHANGELOG exists
echo -e "${GREEN}[4/10] Checking CHANGELOG...${NC}"
if [ -f "CHANGELOG.md" ]; then
    if grep -q "\[$TOML_VERSION\]" CHANGELOG.md; then
        echo "  ✓ CHANGELOG.md has entry for v$TOML_VERSION"
    else
        echo -e "  ${YELLOW}⚠ CHANGELOG.md missing entry for v$TOML_VERSION${NC}"
        WARNINGS=$((WARNINGS + 1))
    fi
else
    echo -e "  ${YELLOW}⚠ CHANGELOG.md not found${NC}"
    WARNINGS=$((WARNINGS + 1))
fi

# Check 5: Build dependencies
echo -e "${GREEN}[5/10] Checking build dependencies...${NC}"
if pip show build > /dev/null 2>&1; then
    echo "  ✓ build installed"
else
    echo -e "  ${YELLOW}⚠ 'build' not installed${NC}"
    echo "    Install with: pip install build"
    WARNINGS=$((WARNINGS + 1))
fi

if pip show twine > /dev/null 2>&1; then
    echo "  ✓ twine installed"
else
    echo -e "  ${YELLOW}⚠ 'twine' not installed${NC}"
    echo "    Install with: pip install twine"
    WARNINGS=$((WARNINGS + 1))
fi

# Check 6: Git status
echo -e "${GREEN}[6/10] Checking git status...${NC}"
if git diff-index --quiet HEAD --; then
    echo "  ✓ No uncommitted changes"
else
    echo -e "  ${YELLOW}⚠ Uncommitted changes detected${NC}"
    WARNINGS=$((WARNINGS + 1))
fi

# Check 7: Git tag
echo -e "${GREEN}[7/10] Checking git tag...${NC}"
if git tag | grep -q "^v$TOML_VERSION$"; then
    echo -e "  ${YELLOW}⚠ Tag v$TOML_VERSION already exists${NC}"
    WARNINGS=$((WARNINGS + 1))
else
    echo "  ✓ Tag v$TOML_VERSION not yet created (will need to create)"
fi

# Check 8: Package structure
echo -e "${GREEN}[8/10] Checking package structure...${NC}"
if [ -d "chaos_sdk" ]; then
    if [ -f "chaos_sdk/__init__.py" ]; then
        echo "  ✓ chaos_sdk/__init__.py exists"
    else
        echo -e "  ${RED}✗ chaos_sdk/__init__.py not found${NC}"
        ERRORS=$((ERRORS + 1))
    fi
else
    echo -e "  ${RED}✗ chaos_sdk directory not found${NC}"
    ERRORS=$((ERRORS + 1))
fi

# Check 9: Clean build directories
echo -e "${GREEN}[9/10] Checking for old build artifacts...${NC}"
if [ -d "dist" ] || [ -d "build" ] || [ -d "chaos_sdk.egg-info" ]; then
    echo -e "  ${YELLOW}⚠ Old build artifacts found (will be cleaned)${NC}"
    WARNINGS=$((WARNINGS + 1))
else
    echo "  ✓ No old build artifacts"
fi

# Check 10: Dependencies
echo -e "${GREEN}[10/10] Verifying dependencies in pyproject.toml...${NC}"
if grep -q "dependencies = \[" pyproject.toml; then
    echo "  ✓ Dependencies section exists"
else
    echo -e "  ${RED}✗ Dependencies section not found${NC}"
    ERRORS=$((ERRORS + 1))
fi

echo ""
echo -e "${YELLOW}====================================${NC}"
echo -e "${YELLOW}   Summary${NC}"
echo -e "${YELLOW}====================================${NC}"

if [ $ERRORS -eq 0 ] && [ $WARNINGS -eq 0 ]; then
    echo -e "${GREEN}✓ All checks passed!${NC}"
    echo ""
    echo -e "${GREEN}Ready to publish version $TOML_VERSION${NC}"
    echo ""
    echo "Next steps:"
    echo "  1. Run: ./scripts/publish.sh test"
    echo "  2. Test installation from TestPyPI"
    echo "  3. Run: ./scripts/publish.sh prod"
    echo "  4. Create git tag: git tag v$TOML_VERSION"
    echo "  5. Push tag: git push origin v$TOML_VERSION"
    exit 0
elif [ $ERRORS -eq 0 ]; then
    echo -e "${YELLOW}⚠ $WARNINGS warning(s) found${NC}"
    echo ""
    echo "You can proceed, but please review the warnings above."
    exit 0
else
    echo -e "${RED}✗ $ERRORS error(s) found${NC}"
    echo -e "${YELLOW}⚠ $WARNINGS warning(s) found${NC}"
    echo ""
    echo "Please fix the errors before publishing."
    exit 1
fi
