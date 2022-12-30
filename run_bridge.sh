#!/bin/bash

MUTEX="/tmp/slack-to-ctis-mutex"
SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )

if test -f $MUTEX;
then
	exit
else
	touch $MUTEX
	cd $SCRIPT_DIR
	RW_CONFIG_PATH="./config_vol/config.yaml" python3 ./src/slack_to_ctis.py
	rm $MUTEX
fi
