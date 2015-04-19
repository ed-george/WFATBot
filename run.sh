#!/bin/bash
## Simple shell script that reboots the bot if it crashes
## Credit to github.com/XSlicer
until python bot.py; do
	echo "CRASH" >&2
	sleep 1
done