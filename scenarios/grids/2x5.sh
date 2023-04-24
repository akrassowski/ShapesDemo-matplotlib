#!/bin/bash -e
#
# startup 2 rows of 1 publisher + 4 subscribers in the right slots

if [ "$1" == "" ]; then
    DOMAIN=27
else
    DOMAIN=$1
fi

TOP_DIR=`readlink -f ../..`
EXE=${TOP_DIR}/src/shapes_demo.py
COMMON="--domain_id $DOMAIN"
TOP_ROW="--subtitle Legacy --ShapeType"
BOTTOM_ROW="--subtitle Extended --ShapeTypeExtended"
LEFT="--subscribe S "
RIGHT="--subscribe CST "

pushd ${TOP_DIR}/src >& /dev/null

FLAGS=(${COMMON} ${TOP_ROW} --config ${TOP_DIR}/scenarios/grids/pub_red_square.cfg --index 1 )
${EXE} "${FLAGS[@]}" &

FLAGS=(--title "Square Domain:${DOMAIN}" ${COMMON} ${TOP_ROW} ${LEFT} --index 2 )
${EXE} "${FLAGS[@]}" &

FLAGS=(--title "Square Domain:${DOMAIN}" ${COMMON} ${TOP_ROW} ${LEFT} --index 3 )
${EXE} "${FLAGS[@]}" &

FLAGS=(--title "All Domain:${DOMAIN}" ${COMMON} ${TOP_ROW} ${RIGHT} --index 4 )
${EXE} "${FLAGS[@]}" &

FLAGS=(--title "All Domain:${DOMAIN}" ${COMMON} ${TOP_ROW} ${RIGHT} --index 5 )
${EXE} "${FLAGS[@]}" &

FLAGS=(--title "Square Domain:${DOMAIN}" ${COMMON} ${BOTTOM_ROW} --config ${TOP_DIR}/scenarios/grids/pub_green_square.cfg --index 6 )
${EXE} "${FLAGS[@]}" &

FLAGS=(--title "Square Domain:${DOMAIN}" ${COMMON} ${BOTTOM_ROW} ${LEFT} --index 7 )
${EXE} "${FLAGS[@]}" &

FLAGS=(--title "All Domain:${DOMAIN}" ${COMMON} ${BOTTOM_ROW} ${LEFT} --index 8 )
${EXE} "${FLAGS[@]}" &

FLAGS=(--title "All Domain:${DOMAIN}" ${COMMON} ${BOTTOM_ROW} ${RIGHT} --index 9 )
${EXE} "${FLAGS[@]}" &

FLAGS=(--title "All Domain:${DOMAIN}" ${COMMON} ${BOTTOM_ROW} ${RIGHT} --index 10 )
${EXE} "${FLAGS[@]}" &


${TOP_DIR}/scenarios/stop.sh

