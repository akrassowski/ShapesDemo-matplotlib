#!/bin/bash -e
#
# startup 4 subscribers in the right slots

if [ "$1" == "" ]; then
    DOMAIN=27
else
    DOMAIN=$1
fi

for N in 2 3 ; do
    CMD="./subAPI.py --domain_id ${DOMAIN} --index $N --no-extended"
    echo $CMD
    $CMD &
done

for N in 5 6; do
    CMD="./subAPI.py --domain_id ${DOMAIN} --index $N --extended"
    echo $CMD
    $CMD &
done

echo "Use pkill Python to kill all Python subscribers (and all other Python!)"
