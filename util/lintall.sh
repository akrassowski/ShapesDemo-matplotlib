#!/bin/bash
#
cd ../src
for T in *.py; do
  # skip linting of generated code
  if [ $T == "ShapeTypeExtended.py" ]; then
    continue
  fi
  pylint ./$T
done
