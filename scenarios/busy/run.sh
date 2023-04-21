#!/bin/bash -e
#

DOMAIN=27

TOP_DIR=`readlink -f ../..`
EXE=${TOP_DIR}/src/shapes_demo.py
COMMON="--domain_id ${DOMAIN} --ShapeTypeExtended --log_level 50 -f 2.375 2.6"
COMMON="--domain_id ${DOMAIN} --ShapeTypeExtended --log_level 50 -f 2.13 2.44" # works

# pub 3 blue
FLAGS=(${COMMON} --subtitle 'Blue Extended' --index 1 --config pub_blue.cfg)
${EXE} "${FLAGS[@]}" &

# pub 3 red 
FLAGS=(${COMMON} --subtitle 'Red Extended' --index 6 --config pub_red.cfg)
${EXE} "${FLAGS[@]}" &

# pub 3 green
FLAGS=(${COMMON} --subtitle 'Green Extended' --index 11 --config pub_green.cfg)
${EXE} "${FLAGS[@]}" &


## SUBSCRIBERS

# all Legacy
FLAGS=(${COMMON} --subtitle 'All Legacy' --ShapeType --index 2 --subscribe cst)
${EXE} "${FLAGS[@]}" &

# all Extended
FLAGS=(${COMMON} --subtitle 'All Extended' --index 7 --subscribe cst)
${EXE} "${FLAGS[@]}" &


# Pair of filters: 
FLAGS=(${COMMON} --subtitle 'Filter Top' --index 8 --config filter_top.cfg)
${EXE} "${FLAGS[@]}" &
FLAGS=(${COMMON} --subtitle 'Filter Bottom' --index 13 --config filter_bottom.cfg)
${EXE} "${FLAGS[@]}" &

# Color Filters
FLAGS=(${COMMON} --subtitle 'Filter Red' --index 4 --config filter_red.cfg)
${EXE} "${FLAGS[@]}" &
FLAGS=(${COMMON} --subtitle 'Filter Blue' --index 9 --config filter_blue.cfg)
${EXE} "${FLAGS[@]}" &
FLAGS=(${COMMON} --subtitle 'Filter Green' --index 14 --config filter_green.cfg)
${EXE} "${FLAGS[@]}" &

# Shape-area Filters
FLAGS=(${COMMON} --subtitle 'Circles Top' --index 5 --config filter_circle_top.cfg)
${EXE} "${FLAGS[@]}" &
FLAGS=(${COMMON} --subtitle 'Square Top' --index 10 --config filter_square_top.cfg)
${EXE} "${FLAGS[@]}" &
FLAGS=(${COMMON} --subtitle 'Triangles Top' --index 15 --config filter_triangle_top.cfg)
${EXE} "${FLAGS[@]}" &

../stop.sh
