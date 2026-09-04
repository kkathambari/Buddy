#!/bin/bash
set -e

echo "Running full test suite..."
APP_ENV=test uv run pytest -v

echo "Running security scan..."
if command -v gitleaks &> /dev/null; then
    gitleaks detect -v
else
    echo "Warning: gitleaks not found in path, skipping secret scan"
fi

echo "Building frontend..."
cd interfaces/web
npm install
npm run lint
npm run build
cd ../..

echo "Validating Docker compose file..."
docker compose -f docker-compose.prod.yml config -q

echo "Release validation complete."
echo "If you're ready, run:"
echo "git tag v1.0.0-rcX"
echo "git push --tags"
