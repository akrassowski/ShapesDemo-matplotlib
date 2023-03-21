#!/bin/bash -e
#
# startup either one of 3 Publishers or the Sub

if [ "$1" == "sub" ]; then
   DO_SUB=1 
   SLOT=7
elif [ "$1" == "10" ]; then
   DO_PUB=10
   SLOT=1
elif [ "$1" == "20" ]; then
   DO_PUB=20
   SLOT=6
elif [ "$1" == "30" ]; then
   DO_PUB=30
   SLOT=11
else
   echo "invoke $0 with these args:"
   echo " sub|10|20|30 [domain]"
   exit
fi
if [ "$2" == "" ]; then
    DOMAIN=27
else
    DOMAIN=$1
fi

TOP_DIR=`readlink -f ../..`
EXE=${TOP_DIR}/src/ShapesDemo.py
COMMON="--domain_id ${DOMAIN} --index ${SLOT} --log_level 50 -f 2.375 2.6"
#COMMON="--domain_id ${DOMAIN} --index ${SLOT} --log_level 50 -f 2.13 2.44" # works
#COMMON="--domain_id ${DOMAIN} --index ${SLOT} --log_level 50 -f 2.26 2.47" # checking
#COMMON="--domain_id ${DOMAIN} --index ${SLOT} --log_level 50 "
QOS="--qos_file RedundancyDemo${DO_PUB}.xml --config RedundancyDemo${DO_PUB}.cfg"

if [ "$DO_SUB" == 1 ]; then
  FLAGS=(${COMMON} --subtitle Subscriber -sub s --qos_file RedundancyDemo10.xml )
else 
  FLAGS=(${COMMON} --subtitle "Strength ${DO_PUB}" ${QOS} )
fi

echo ${EXE} "${FLAGS[@]}" 
${EXE} "${FLAGS[@]}" 


