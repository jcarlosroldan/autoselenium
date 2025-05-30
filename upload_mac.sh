#!/bin/bash

# Remove auxiliary files
rm -rf build dist autoselenium.egg-info
find . -type d -name 'autoselenium-*' -exec rm -rf {} +

# Commit changes
git add .
git commit
git push origin master

# Build docs
sphinx-apidoc -o docs autoselenium -f --separate

# Update library
python3 setup.py sdist bdist_wheel

echo 'Enter your PyPI API token:'
read -s PYPI_TOKEN
echo

TWINE_PASSWORD="$PYPI_TOKEN" TWINE_USERNAME=__token__ python3 -m twine upload dist/*

# Remove auxiliary files again
rm -rf build dist autoselenium.egg-info
find . -type d -name 'autoselenium-*' -exec rm -rf {} +

# Wait for 5 seconds
sleep 5

# Reinstall it
sudo dscacheutil -flushcache
sudo killall -HUP mDNSResponder
pip3 uninstall autoselenium -y
pip3 install autoselenium -U

echo 'Script execution completed.'