#!/bin/bash
cd /home/vps/pulsebnb
exec ./venv/bin/uvicorn api:app --host 127.0.0.1 --port 8093
