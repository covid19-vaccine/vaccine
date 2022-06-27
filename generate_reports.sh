#!/bin/bash -e
cd ~/source/esr21
source ~/.venvs/esr21/bin/activate  # if you use venv
python manage.py populate_graphs 

# step 1 : chmod +x generate_reports.sh
# step 2 : crontab -e */5 * * * * generate_reports.sh