#!/bin/bash
echo "===================================================="
echo "    ANDROID APK COMPILER (BUILDOZER) AUTOMATION     "
echo "===================================================="
echo "Please enter your Linux/WSL password below to authorize:"
sudo apt update

# Install dependencies specifically formatted for Ubuntu 24.04 (Noble)
sudo apt install -y git zip unzip openjdk-17-jdk python3-pip python3-venv python3.12-venv autoconf libtool pkg-config zlib1g-dev libncurses-dev cmake libffi-dev libssl-dev

cd "$(dirname "$0")"

# Create and activate a virtual environment
python3 -m venv .build_venv
source .build_venv/bin/activate

pip install --upgrade pip
pip install buildozer cython virtualenv

echo ""
echo "Dependencies installed! Initializing Buildozer..."

if [ ! -f "buildozer.spec" ]; then
    buildozer init
    # Update requirements to include our AI libraries
    sed -i 's/requirements = python3,kivy/requirements = python3,kivy,openai,anthropic,google-generativeai,requests/' buildozer.spec
    sed -i 's/title = My Application/title = DevBuddy/' buildozer.spec
    sed -i 's/package.name = myapp/package.name = devbuddy/' buildozer.spec
    sed -i 's/package.domain = org.test/package.domain = com.kkath/' buildozer.spec
fi

echo ""
echo "===================================================="
echo "    STARTING APK COMPILATION! This will take a while."
echo "    (Around 10-15 minutes on the first run)          "
echo "===================================================="

buildozer android debug

echo "===================================================="
echo "    COMPILATION FINISHED!"
echo "    If successful, your APK is in the 'bin' folder."
echo "===================================================="
echo "Press any key to close this window."
read -n 1
