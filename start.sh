#!/bin/bash
# Install Chrome
apt-get update
apt-get install -y wget gnupg unzip

wget -q https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
apt-get install -y ./google-chrome-stable_current_amd64.deb

# Install Chromedriver matching Chrome version
CHROME_VERSION=$(google-chrome --version | sed 's/Google Chrome //')
CHR_VERSION=$(echo $CHROME_VERSION | cut -d '.' -f 1)

wget -q https://chromedriver.storage.googleapis.com/$CHR_VERSION.0.0/chromedriver_linux64.zip
unzip chromedriver_linux64.zip -d /usr/local/bin/

chmod +x /usr/local/bin/chromedriver

# Start FastAPI
uvicorn main:app --host 0.0.0.0 --port "$PORT"
