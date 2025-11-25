#!/bin/bash
# ===============================================
# 🧩 Codex Template Unpacker — Delimited Bundle with Versioned Output
# ===============================================
# Usage:
#   ./extract-md-bundle.sh ./dist/codex-templates-44.zip
# Result:
#   - ./dist/codex-template-bundle-44/
#       - codex-template-bundle-44.md  ← ✅ versioned name
#       - README.md
#       - codex-template-44.lock
#       - SCROLL-TEMPLATE-UPLOAD-44.md
#       - non-.md extras
# ===============================================

PACKAGE_ZIP="$1"

if [[ -z "$PACKAGE_ZIP" ]]; then
  echo "❌ Usage: ./extract-md-bundle.sh ./dist/codex-templates-XX.zip"
  exit 1
fi

if [[ ! -f "$PACKAGE_ZIP" ]]; then
  echo "❌ File not found: $PACKAGE_ZIP"
  exit 1
fi

CONFIG_FILE="./mkpkg.config"

# === Load Config ===
if [[ ! -f "$CONFIG_FILE" ]]; then
  echo "❌ Config file not found: $CONFIG_FILE"
  exit 1
fi
source "$CONFIG_FILE"

# === Extract version number from filename
ZIP_BASENAME=$(basename "$PACKAGE_ZIP")
PACKAGE_VERSION=$(echo "$ZIP_BASENAME" | sed -E 's/^codex-templates-([0-9a-zA-Z]+)\.zip$/\1/')

# === Validate Config Values ===
REQUIRED_VARS=("BATCH_TXT_PROTOCOL_SRC" "CURRENT_USER" "NON_TEMPLATE_PATTERNS" "PACKAGE_OUTPUT_DIR" "REG_FILE_NAME")
for var in "${REQUIRED_VARS[@]}"; do
  if [[ -z "${!var}" ]]; then
    echo "❌ Missing required config variable: $var"
    exit 1
  fi
done

BATCH_TXT_PROTOCOL_FILENAME_WITH_EXT=$(basename "$BATCH_TXT_PROTOCOL_SRC")
BATCH_TXT_PROTOCOL_FILENAME_NO_EXT="${BATCH_TXT_PROTOCOL_FILENAME_WITH_EXT%.*}"
BATCH_TXT_PROTOCOL_FILE_EXT="${BATCH_TXT_PROTOCOL_FILENAME_WITH_EXT##*.}"
BATCH_TXT_PROTOCOL_OUT="${PACKAGE_OUTPUT_DIR}/${BATCH_TXT_PROTOCOL_FILENAME_NO_EXT}-${PACKAGE_VERSION}.${BATCH_TXT_PROTOCOL_FILE_EXT}"


if [[ -z "$PACKAGE_VERSION" ]]; then
  echo "❌ Could not extract version number from $ZIP_BASENAME"
  exit 1
fi

# === Set output folder and versioned bundle filename
BUNDLE_DIR="$PACKAGE_OUTPUT_DIR/codex-template-bundle-$PACKAGE_VERSION"
BUNDLE_FILE="$BUNDLE_DIR/codex-template-bundle-$PACKAGE_VERSION.txt"

echo "🌀 Creating bundle folder: $BUNDLE_DIR"
mkdir -p "$BUNDLE_DIR"

# === Create temporary extraction workspace
TEMP_DIR=$(mktemp -d)
unzip -q "$PACKAGE_ZIP" -d "$TEMP_DIR"

REG_SRC="$TEMP_DIR/$REG_FILE_NAME"
REG_VER=$(grep '^version:' "$REG_SRC" | head -n1 | awk -F '"' '{print $2}')

# === Begin bundle
echo "🪶 Writing delimited template bundle to: $BUNDLE_FILE"
rm -f "$BUNDLE_FILE"
touch "$BUNDLE_FILE"

TEMPLATE_COUNT=0

for f in "$TEMP_DIR"/*.md; do
  fname=$(basename "$f")

  # Check against exclusion list
  skip_file=false
  for pat in "${NON_TEMPLATE_PATTERNS[@]}"; do
    if [[ "$fname" == $pat ]]; then
      skip_file=true
      break
    fi
  done
  if $skip_file; then
    continue
  fi

  # Count and bundle
  ((TEMPLATE_COUNT++))
  echo "<!-- TEMPLATE-BEGIN: $fname -->" >> "$BUNDLE_FILE"
  cat "$f" >> "$BUNDLE_FILE"
  echo "" >> "$BUNDLE_FILE"
  echo "<!-- TEMPLATE-END $fname -->" >> "$BUNDLE_FILE"
  echo "" >> "$BUNDLE_FILE"
done

echo "🧮 Total templates bundled: $TEMPLATE_COUNT"

echo "✅ Template bundle created: $BUNDLE_FILE"

# === Copy all *.md protocol files (README, scrolls, lockfile)
cp "$TEMP_DIR"/README.md "$BUNDLE_DIR/" 2>/dev/null
cp "$TEMP_DIR"/codex-template-*.md "$BUNDLE_DIR/" 2>/dev/null
cp "$TEMP_DIR"/SCROLL-TEMPLATE-UPLOAD-*.md "$BUNDLE_DIR/" 2>/dev/null

# === Copy all non-.md files (registry, etc)
find "$TEMP_DIR" -maxdepth 1 -type f ! -name "*.md" -exec cp {} "$BUNDLE_DIR/" \;

# ===============================================
# 📝 BUILD BATCH_TXT_PROTOCOL_SRC (with block injection)
# ===============================================
if [[ ! -f "$BATCH_TXT_PROTOCOL_SRC" ]]; then
  echo "⚠️ Codex-Bootstrap source not found: $BATCH_TXT_PROTOCOL_SRC"
  exit 1
fi

sed -e "s/\[REG_VER\]/$REG_VER/g" \
    -e "s/\[CURRENT_USER\]/$CURRENT_USER/g" \
    -e "s/\[TEMPLATE_COUNT\]/$TEMPLATE_COUNT/g" \
    -e "s/\[VER\]/$PACKAGE_VERSION/g" "$BATCH_TXT_PROTOCOL_SRC" > "$BATCH_TXT_PROTOCOL_OUT"

# === Cleanup
rm -rf "$TEMP_DIR"

echo "📦 Bundle folder ready: $BUNDLE_DIR"
