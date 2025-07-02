#!/bin/bash
echo "Hello from the script!"
source /home/ash/mind/mind/env/bin/activate
# cd /home/ash/mind/temp/
python3.11 -m mind.launcher --solver ipopt --exec
