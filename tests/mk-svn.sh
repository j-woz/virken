#!/bin/sh
set -eu

THIS=$( dirname $0 )
cd $THIS

svnadmin create SVN
svn co file:///$PWD/SVN work.svn

cd work.svn
echo HI > f.txt
svn add f.txt
svn commit -m "Start" f.txt

