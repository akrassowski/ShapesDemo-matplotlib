#!/bin/bash
#
cd ../src
for T in test*.py; do
  echo $T
  ./$T
done
