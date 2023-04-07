#!/bin/bash -e
#

read -p $'Hit any key to kill all Python processes\n' -n 1 yn

if [ "$OS" == "Windows_NT" ]; then
  taskkill -F -IM python*
else
  pkill Python
fi
