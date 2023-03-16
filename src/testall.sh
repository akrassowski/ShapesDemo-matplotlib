#!/bin/bash
#
for T in test*.py; do
  echo $T
  ./$T
done
