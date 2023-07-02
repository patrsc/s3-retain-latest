#!/bin/bash
SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
cd "$SCRIPT_DIR"

name="$1"
envfile="$name.env"
logfile="$name.log"

docker run --env-file "$envfile" s3-retain 2>> "$logfile" || exit 1
