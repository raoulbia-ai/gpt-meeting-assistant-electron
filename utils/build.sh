#!/bin/bash

# Exit immediately if a command exits with a non-zero status.
set -e

echo "Starting the Electron application build process..."

# --- Configuration ---
# Add any specific configurations here if needed

# --- Build Instructions ---
echo "--------------------------------------------------"
echo "Build Script Usage:"
echo ""
echo "This script builds the Electron application for the detected operating system."
echo ""
echo "To build for the current OS:"
echo "  ./utils/build.sh"
echo ""
echo "To force a build for a specific platform:"
echo "  ./utils/build.sh --linux  # Build for Linux"
echo ""
echo "Note: Cross-compiling (e.g., building for Linux on Windows) might require"
echo "additional setup like Docker. Refer to the electron-builder documentation."
echo "--------------------------------------------------"

# --- OS Detection and Target Platform ---
TARGET_PLATFORM=""
FORCE_PLATFORM=$1 # Check for command-line argument

if [[ "$FORCE_PLATFORM" == "--linux" ]]; then
    echo "Forcing build for Linux..."
    TARGET_PLATFORM="--linux"
elif [[ -z "$FORCE_PLATFORM" ]]; then # Only detect OS if no platform is forced
    # Detect OS if no platform is forced
    OS_NAME=$(uname -s)
    echo "Detecting Operating System..."
    if [[ "$OS_NAME" == "Linux" ]]; then
        echo "Detected OS: Linux"
        TARGET_PLATFORM="--linux"
    # Add elif for macOS if needed: elif [[ "$OS_NAME" == "Darwin" ]]; then TARGET_PLATFORM="--mac"
    else
        echo "Unsupported OS detected ($OS_NAME) or no specific target forced."
        echo "electron-builder will build for the current platform by default."
        # Let electron-builder decide based on the current environment
        TARGET_PLATFORM="" # Let electron-builder handle it, but it won't be forced to --win
    fi
else # A platform was forced, but it wasn't --linux (or was empty but not caught by -z somehow)
    echo "Unsupported forced platform: $FORCE_PLATFORM. Only --linux is supported."
    echo "electron-builder will build for the current platform by default."
    TARGET_PLATFORM="" # Let electron-builder handle it
fi

# --- Dependency Installation ---
echo "Step 1: Installing project dependencies..."
npm install
if [ $? -ne 0 ]; then
    echo "Error: Failed to install dependencies."
    exit 1
fi
echo "Dependencies installed successfully."

# --- Frontend Build ---
# Check if a 'build' script exists in package.json before running it
echo "Step 2: Building frontend assets (if applicable)..."
if npm run | grep -q -E '^[[:space:]]+build[[:space:]]*$'; then
    npm run build
    if [ $? -ne 0 ]; then
        echo "Error: Frontend build failed."
        exit 1
    fi
    echo "Frontend built successfully."
else
    echo "No 'npm run build' script found in package.json. Skipping frontend build."
fi

# --- Electron Build ---
echo "Step 3: Building Electron application package..."
if [ -z "$TARGET_PLATFORM" ]; then
    echo "Building for the current platform (default)..."
else
    echo "Building specifically for target: $TARGET_PLATFORM"
fi

# Use npx to ensure electron-builder is accessible
npx electron-builder $TARGET_PLATFORM
icacls dist/win-unpacked/openai-virtual-prompter.exe /grant Everyone:RX
if [ $? -ne 0 ]; then
    echo "Error: electron-builder failed."
    exit 1
fi

echo "--------------------------------------------------"
echo "Build process completed successfully!"
echo "Distribution packages can be found in the 'dist' directory."
echo "--------------------------------------------------"

exit 0