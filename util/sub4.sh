#!/bin/bash -e
#
# startup 4 subscribers in the right slots

if [ "$1" == "" ]; then
    DOMAIN=27
else
    DOMAIN=$1
fi

EXE=./PubSubApp.py
COMMON="--domain_id $DOMAIN"
TOP_ROW="--subtitle Legacy --no-extended"
BOTTOM_ROW="--subtitle Extended --extended"
LEFT="--subscribe S"
RIGHT="--subscribe CST"

FLAGS=(--title "Square Domain:${DOMAIN}" ${COMMON} ${TOP_ROW} ${LEFT} --index 2 )
${EXE} "${FLAGS[@]}" &

FLAGS=(--title "All Domain:${DOMAIN}" ${COMMON} ${TOP_ROW} ${RIGHT} --index 3 )
${EXE} "${FLAGS[@]}" &

FLAGS=(--title "Square Domain:${DOMAIN}" ${COMMON} ${BOTTOM_ROW} ${LEFT} --index 5 )
${EXE} "${FLAGS[@]}" &

FLAGS=(--title "All Domain:${DOMAIN}" ${COMMON} ${BOTTOM_ROW} ${RIGHT} --index 6 )
${EXE} "${FLAGS[@]}" &


echo "Use pkill Python to kill all Python subscribers (and all other Python!)"
