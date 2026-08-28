#!/bin/bash

# SPDX-FileCopyrightText: Copyright (c) 2025-2026 Almaz Ilaletdinov <a.ilaletdinov@yandex.ru>
# SPDX-License-Identifier: MIT

COLOR=$1
NGINX_SITE="/etc/nginx/sites-available/test-radar.ilaletdinov.ru"

if [ -z "$COLOR" ]; then
    echo "Usage: $0 {blue|green}"
    exit 1
fi

if [ "$COLOR" == "blue" ]; then
    PORT="8012"
elif [ "$COLOR" == "green" ]; then
    PORT="8013"
else
    echo "Invalid color. Use 'blue' or 'green'"
    exit 1
fi

echo "Switching to $COLOR (port $PORT)"

if ! curl -s -f "http://127.0.0.1:$PORT/health/" > /dev/null; then
    echo "ERROR: $COLOR environment is not healthy!"
    echo "Health check failed for http://127.0.0.1:$PORT/health/"
    exit 1
fi

sudo sed -i "s/set \$backend \"127.0.0.1:[0-9]\\{4\\}\";/set \$backend \"127.0.0.1:$PORT\";/g" $NGINX_SITE
sudo nginx -t || exit 1
sudo systemctl reload nginx

echo "Successfully switched to $COLOR environment (port $PORT)"
