#!/bin/zsh
set -eu

if [[ ${#*} != 1 ]]
then
  print "Provide count N!"
  return 1
fi

N=$1

integer -Z 2 i
for (( i=0 ; i<N ; i++ ))
do
  touch f${i}.txt
done
