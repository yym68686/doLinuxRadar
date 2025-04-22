#!/bin/bash
set -eu
rm -rf /app/doLinuxRadar
git clone --recurse-submodules --depth 1 -b main --quiet https://github.com/yym68686/doLinuxRadar.git
source /usr/local/bin/activate
python -u /app/doLinuxRadar/bot.py