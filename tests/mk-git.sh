#!/bin/sh
set -eu

set -x
mkdir -pv work.git
cd work.git
git init

echo HI > f.txt
git add f.txt
git commit -m "First" f.txt
