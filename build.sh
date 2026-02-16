#!/bin/bash
# X Knowledge Graph - Linux Build Script
# Creates tar archive for VPS deployment

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Read version (remove leading 'v' if present)
VERSION=$(cat VERSION.txt | sed 's/^v//')
DIST_DIR="distributions"
APP_NAME="x-knowledge-graph-v${VERSION}"

echo "========================================"
echo "  X Knowledge Graph - Linux Build"
echo "========================================"
echo "Version: $VERSION"
echo ""

# Clean previous build
echo "Cleaning previous builds..."
rm -rf "$DIST_DIR/$APP_NAME"
rm -f "$DIST_DIR/$APP_NAME.tar"

# Create directory
mkdir -p "$DIST_DIR/$APP_NAME"

# Copy required files
echo "Copying application files..."
cp main.py "$DIST_DIR/$APP_NAME/"
cp VERSION.txt "$DIST_DIR/$APP_NAME/"
cp -r core "$DIST_DIR/$APP_NAME/"
cp -r frontend "$DIST_DIR/$APP_NAME/"
cp -r test_data "$DIST_DIR/$APP_NAME/"
cp requirements.txt "$DIST_DIR/$APP_NAME/" 2>/dev/null || true

# Create tar archive
echo "Creating archive..."
tar -cf "$DIST_DIR/$APP_NAME.tar" -C "$DIST_DIR" "$APP_NAME"

# Generate SHA256 checksum
echo "Generating SHA256 checksum..."
sha256sum "$DIST_DIR/$APP_NAME.tar" > "$DIST_DIR/$APP_NAME.tar.sha256"

# Show result
if [ -f "$DIST_DIR/$APP_NAME.tar" ]; then
    SIZE=$(du -h "$DIST_DIR/$APP_NAME.tar" | cut -f1)
    echo ""
    echo "========================================"
    echo "  BUILD SUCCESSFUL"
    echo "========================================"
    echo "Archive: $DIST_DIR/$APP_NAME.tar"
    echo "Size: $SIZE"
    echo "Checksum: $DIST_DIR/$APP_NAME.tar.sha256"
    echo ""
    echo "To deploy to VPS:"
    echo "  scp $DIST_DIR/$APP_NAME.tar user@host:/projects/"
    echo ""
    echo "On VPS:"
    echo "  cd /projects"
    echo "  tar -xf $APP_NAME.tar"
    echo "  cd $APP_NAME"
    echo "  python main.py &"
else
    echo "BUILD FAILED!"
    exit 1
fi
