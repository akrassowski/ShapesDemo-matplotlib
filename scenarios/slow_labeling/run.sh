#!/bin/bash -e
#

DOMAIN=27

TOP_DIR=`readlink -f ../..`
EXE=${TOP_DIR}/src/shapes_demo.py
COMMON="--domain_id ${DOMAIN} --log_level 50 -f 2.375 2.6"
COMMON="--domain_id ${DOMAIN} --log_level 50 -f 2.13 2.44" # works

# pub 3 slowly
FLAGS=(${COMMON} --subtitle 'Subtitle 1Hz' --index 1 --publish_rate 1000
   --text '20 20 circle blue 20 oblique bold,
           50 50 square cyan 15 italic bold,
           80 80 triangle orange 10'
   --config pub_three.cfg)
${EXE} "${FLAGS[@]}" &

## SUBSCRIBERS

FLAGS=(${COMMON} --subtitle 'normal subtitle' --index 3 --subscribe cst)
${EXE} "${FLAGS[@]}" &

../stop.sh
