# HACK FOR FUN

A terminal-based public greeting-link generator for Termux and Linux.

Instagram: cybergenius.io

## Features
- Birthday greetings
- YouTube video pages
- Social-themed pages
- Festival greetings
- Public HTTPS links through ngrok
- Optional, clearly disclosed device check-in

## Install on Termux
    pkg update
    pkg install python git -y
    git clone https://github.com/ZAIDU704/Hack-For-Fun.git
    cd Hack-For-Fun
    bash install.sh

## Run
    python main.py

## Hosting
Choose ngrok from the menu for a temporary public HTTPS link. Keep the
tool running while the link is in use. For permanent hosting, deploy the
Flask app to a Python-capable cloud service.

## Privacy
The check-in page explains what is collected. The visitor must check the
consent box and press Start Check before the camera and location are
requested. Nothing is captured automatically on page load.

Camera and location require browser permission and HTTPS for public use.
Collected check-in photos and coordinates are sensitive: secure the server
and delete submissions when no longer needed.
