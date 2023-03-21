#!/bin/bash

BIN=./_redun.sh

$BIN  sub >& sub.out &

$BIN  10 >& pub10.out &
$BIN  20 >& pub20.out &
$BIN  30 >& pub30.out &

echo "Use pkill Python to kill all Python subscribers (and all other Python!)"
echo Command is queued, just hit y to stop
read -p "Hit any key to kill all Python processes" -n 1 yn
pkill Python
