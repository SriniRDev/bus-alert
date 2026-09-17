#!/bin/bash
cd ${HOME}/workfolder_temp/bus-alert
source .venv/bin/activate
python3 main.py >> bus-alert.log 2>&1