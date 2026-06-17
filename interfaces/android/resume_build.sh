#!/bin/bash
echo "===================================================="
echo "    RESUMING ANDROID APK COMPILATION                "
echo "===================================================="

cd "$(dirname "$0")"

# Activate the virtual environment
source .build_venv/bin/activate

# Because the network dropped, the NDK zip file is likely corrupted or partially downloaded.
# Let's delete the partial download so it can start fresh!
echo "Cleaning up partial downloads..."
rm -f ~/.buildozer/android/platform/*ndk*.zip

echo ""
echo "Resuming buildozer..."
buildozer android debug

echo "===================================================="
echo "    COMPILATION FINISHED!"
echo "    If successful, your APK is in the 'bin' folder."
echo "===================================================="
echo "Press any key to close this window."
read -n 1
