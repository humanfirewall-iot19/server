#!/bin/sh

env TELEGRAM_TOKEN=$TELEGRAM_TOKEN PORT=8080 nohup python3 run.py > /dev/null &
