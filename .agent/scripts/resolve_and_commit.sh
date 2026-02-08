#!/bin/bash
git add frontend/
git add backend/logs/price_debug.log
git commit -m "Resolved merge conflict in price_debug.log and updated frontend pages with standardized navigation bars"
git stash drop
