#!/bin/bash -e
#
# Just start 1 publisher

if [ "$1" == "" ]; then
    DOMAIN=27
else
    DOMAIN=$1
fi

cd ../src
EXE=../src/shapes_demo.py
COMMON="--domain_id $DOMAIN"
TOP_ROW="--subtitle Legacy --ShapeType"

FLAGS=(${COMMON} ${TOP_ROW} --publish S --index 1 )
echo ${EXE} "${FLAGS[@]}" &
${EXE} "${FLAGS[@]}" &

exit

