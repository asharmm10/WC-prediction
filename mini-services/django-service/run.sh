#!/bin/bash
cd /home/z/my-project/worldcup
while true; do
    python3 manage.py runserver 0.0.0.0:8000 --noreload 2>&1
    echo "Django stopped, restarting in 2 seconds..." >&2
    sleep 2
done
