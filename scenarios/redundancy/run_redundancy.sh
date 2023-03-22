#!/bin/bash

BIN=./_redun.sh

$BIN  sub >& sub.out &

$BIN  10 >& pub10.out &
$BIN  20 >& pub20.out &
$BIN  30 >& pub30.out &

../stop.sh
