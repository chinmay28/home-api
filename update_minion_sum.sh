#!/bin/bash

date

# Paths
MAGIC_CMD="/home/chinmay/home-api/magic -mode lookup -dir /home/chinmay/home-api/secrets/ -sum"
MAX_RETRIES=2
SUM=0

# Retry loop
for ((i=0; i<=MAX_RETRIES; i++)); do
    CMD_OUTPUT=$($MAGIC_CMD 2>/dev/null)
    SUM=$CMD_OUTPUT

    echo "Attempt $((i+1)): Sum = $SUM"

    if [[ "$SUM" != "0" && -n "$SUM" ]]; then
        break
    fi

    sleep 10
done

# Construct JSON
JSON=$(jq -nc --arg sum "$SUM" '{"value": {"sum":$sum}}')

# Send to FastAPI
curl -X POST http://127.0.0.1:8000/api/minion-sum \
     -H "Content-Type: application/json" \
     -d "$JSON"

date
