#!/bin/bash -e
#
# startup 1 LARGE publisher and 1 LARGE subscriber

if [ "$1" == "" ]; then
    DOMAIN=27
else
    DOMAIN=$1
fi

TOP_DIR=`readlink -f ../..`
EXE=${TOP_DIR}/src/shapes_demo.py
COMMON="--domain_id $DOMAIN"
SIZE="-f 6.5 8.0"
PUB="--publish CST "
SUB="--subscribe CST "
POS2="--position 700 0"
pushd ${TOP_DIR}/src >& /dev/null

#FLAGS=(${COMMON} ${PUB} ${SIZE} --config ${TOP_DIR}/scenarios/grids/pub_red_square.cfg )
FLAGS=(${COMMON} ${PUB} ${SIZE} --ticks )
${EXE} "${FLAGS[@]}" &

FLAGS=(--title "Square Domain:${DOMAIN}" ${COMMON} ${SUB} ${SIZE} ${POS2} )
${EXE} "${FLAGS[@]}" &


${TOP_DIR}/scenarios/stop.sh

