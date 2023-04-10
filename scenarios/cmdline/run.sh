#!/bin/bash -e
#

DOMAIN=27

EXE=../../src/shapes_demo.py
COMMON="--domain_id ${DOMAIN} --log_level 50 " # works

# sub legacy
FLAGS=(${COMMON} --subtitle 'Legacy' --ShapeType --index 3 -sub cst)
${EXE} "${FLAGS[@]}" &

# pub Extended
FLAGS=(${COMMON} --subtitle 'Extended' --index 6 -pub cst)
${EXE} "${FLAGS[@]}" &

# sub legacy
FLAGS=(${COMMON} --subtitle 'Extended' --index 8 -sub cst)
${EXE} "${FLAGS[@]}" &


../stop.sh
