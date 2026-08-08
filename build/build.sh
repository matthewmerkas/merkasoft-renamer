#!/usr/bin/env bash
set -e

# Change working directory to project root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$PROJECT_ROOT"

APP_NAME="Merkasoft Renamer"
SPEC_FILE="build/pyinstaller/MerkasoftRenamer.spec"
DIST_DIR="build/dist"
WORK_DIR="build/work"

# Color outputs
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

run_pyinstaller() {
    echo -e "${BLUE}=== Running PyInstaller ===${NC}"
    mkdir -p "$DIST_DIR" "$WORK_DIR"

    if [ -f "$SPEC_FILE" ]; then
        echo "Using spec file: $SPEC_FILE"
        pyinstaller --noconfirm --clean \
            --distpath "$DIST_DIR" \
            --workpath "$WORK_DIR" \
            "$SPEC_FILE"
    else
        echo "Spec file not found. Building from main.py..."
        pyinstaller --noconfirm --clean --onedir --windowed \
            --name "$APP_NAME" \
            --specpath "build/pyinstaller" \
            --distpath "$DIST_DIR" \
            --workpath "$WORK_DIR" \
            main.py
    fi
}

build_macos() {
    echo -e "${GREEN}========================================${NC}"
    echo -e "${GREEN}    Building macOS Target (.app)        ${NC}"
    echo -e "${GREEN}========================================${NC}"

    if [[ "$OSTYPE" != "darwin"* ]]; then
        echo -e "${RED}Error: macOS target must be built on macOS.${NC}"
        return 1
    fi

    run_pyinstaller

    if [ -d "${DIST_DIR}/${APP_NAME}.app" ]; then
        echo -e "${GREEN}Success! Bundle created at: ${DIST_DIR}/${APP_NAME}.app${NC}"
    else
        echo -e "${GREEN}Success! Executable created at: ${DIST_DIR}/${APP_NAME}/${NC}"
    fi
}

build_linux() {
    echo -e "${GREEN}========================================${NC}"
    echo -e "${GREEN}   Building Linux Target (AppImage)     ${NC}"
    echo -e "${GREEN}========================================${NC}"

    # Handle building Linux target from macOS via Docker
    if [[ "$OSTYPE" != "linux"* ]]; then
        if [[ "$OSTYPE" == "darwin"* ]]; then
            echo -e "${BLUE}macOS host detected. Checking for Docker...${NC}"
            if command -v docker >/dev/null 2>&1 && docker info >/dev/null 2>&1; then
                echo -e "${BLUE}Docker is running. Spawning x86_64 Linux container...${NC}"

                docker run --rm \
                    --platform linux/amd64 \
                    -v "$PROJECT_ROOT:/app" \
                    -w /app \
                    python:3.14-slim \
                    bash -c "
                        set -e
                        echo '=== Installing Linux C-dependencies ==='
                        apt-get update && apt-get install -y --no-install-recommends \
                            curl file binutils squashfs-tools p7zip-full libgl1 libglib2.0-0 libegl1 libdbus-1-3

                        echo '=== Installing Python dependencies inside container ==='
                        pip install --no-cache-dir --upgrade pip
                        if [ -f requirements.txt ]; then
                            pip install --no-cache-dir -r requirements.txt
                        fi
                        pip install --no-cache-dir pyinstaller

                        echo '=== Triggering Linux build ==='
                        ./build/build.sh --linux
                    "
                return 0
            else
                echo -e "${RED}Error: Docker is not installed or not running. Cannot build Linux target on macOS without Docker.${NC}"
                return 1
            fi
        else
            echo -e "${RED}Error: Linux AppImage must be built on Linux or macOS with Docker.${NC}"
            return 1
        fi
    fi

    # Native Linux Build Steps
    run_pyinstaller

    APPDIR="build/dist/MerkasoftRenamer.AppDir"
    TOOL_DIR="build/appimage"
    TOOL_PATH="${TOOL_DIR}/appimagetool-x86_64.AppImage"
    EXTRACTED_TOOL="${TOOL_DIR}/squashfs-root/AppRun"

    echo -e "${BLUE}=== Assembling AppDir structure ===${NC}"
    rm -rf "$APPDIR"
    mkdir -p "$APPDIR/usr/bin"
    cp -r "${DIST_DIR}/${APP_NAME}/"* "$APPDIR/usr/bin/"

    cat << EOF > "$APPDIR/AppRun"
#!/bin/sh
HERE="\$(dirname "\$(readlink -f "\${0}")")"
exec "\${HERE}/usr/bin/${APP_NAME}" "\$@"
EOF
    chmod +x "$APPDIR/AppRun"

    cat << EOF > "$APPDIR/merkasoft-renamer.desktop"
[Desktop Entry]
Name=Merkasoft Renamer
Exec="${APP_NAME}"
Icon=app
Type=Application
Categories=Utility;
EOF

    if [ -f "assets/icon.png" ]; then
        cp assets/icon.png "$APPDIR/app.png"
    fi

    # Download and extract appimagetool
    if [ ! -f "$EXTRACTED_TOOL" ]; then
        echo -e "${BLUE}=== Downloading appimagetool ===${NC}"
        mkdir -p "$TOOL_DIR"
        curl -L --create-dirs -o "$TOOL_PATH" https://github.com/AppImage/appimagetool/releases/download/continuous/appimagetool-x86_64.AppImage

        echo -e "${BLUE}=== Extracting appimagetool payload ===${NC}"
        rm -rf "${TOOL_DIR}/squashfs-root"

        if command -v 7z >/dev/null 2>&1; then
            7z x "$TOOL_PATH" -o"${TOOL_DIR}/squashfs-root" -y >/dev/null
        else
            python3 -c "
with open('$TOOL_PATH', 'rb') as f:
    data = f.read()
offset = -1
for i in range(0, len(data) - 4, 512):
    if data[i:i+4] == b'hsqs':
        offset = i
        break
if offset == -1:
    raise ValueError('Valid SquashFS header not found')
with open('${TOOL_DIR}/appimagetool.squashfs', 'wb') as out:
    out.write(data[offset:])
"
            unsquashfs -d "${TOOL_DIR}/squashfs-root" "${TOOL_DIR}/appimagetool.squashfs"
            rm -f "${TOOL_DIR}/appimagetool.squashfs"
        fi

        chmod -R +x "${TOOL_DIR}/squashfs-root"
    fi

    echo -e "${BLUE}=== Packaging AppImage ===${NC}"
    ARCH=x86_64 "$EXTRACTED_TOOL" "$APPDIR" "${DIST_DIR}/MerkasoftRenamer-x86_64.AppImage"

    echo -e "${GREEN}Success! AppImage created at: ${DIST_DIR}/MerkasoftRenamer-x86_64.AppImage${NC}"
}

build_windows() {
    echo -e "${GREEN}========================================${NC}"
    echo -e "${GREEN}     Building Windows Target (.exe)     ${NC}"
    echo -e "${GREEN}========================================${NC}"

    if [[ "$OSTYPE" != "msys" && "$OSTYPE" != "cygwin" && "$OSTYPE" != "win32" ]]; then
        echo -e "${RED}Error: Windows target must be built on Windows.${NC}"
        return 1
    fi

    run_pyinstaller

    echo -e "${GREEN}Success! Executable created at: ${DIST_DIR}/${APP_NAME}/${NC}"
}

TARGET="${1:-auto}"

case "$TARGET" in
    --macos|macos) build_macos ;;
    --linux|linux) build_linux ;;
    --windows|windows) build_windows ;;
    --all|all)
        build_macos || true
        build_linux || true
        build_windows || true
        ;;
    auto)
        case "$OSTYPE" in
            darwin*) build_macos ;;
            linux*) build_linux ;;
            msys*|cygwin*|win32*) build_windows ;;
            *) echo -e "${RED}Unknown OS: $OSTYPE${NC}"; exit 1 ;;
        esac
        ;;
    *)
        echo "Usage: $0 [--auto | --macos | --linux | --windows | --all]"
        exit 1
        ;;
esac
